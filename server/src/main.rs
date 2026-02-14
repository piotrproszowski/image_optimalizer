use axum::{
    extract::{Multipart, Path as AxumPath, State},
    http::{header, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;
use tower_http::cors::{Any, CorsLayer};
use tower_http::services::ServeDir;
use tracing::{error, info};
use uuid::Uuid;

mod processing;
use processing::{ImageProcessor, ProcessingConfig};

use mimalloc::MiMalloc;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

// State structures
#[derive(Clone)]
struct AppState {
    jobs: Arc<RwLock<std::collections::HashMap<String, JobStatus>>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct JobStatus {
    id: String,
    total: usize,
    processed: usize,
    status: String,
    output_files: Vec<String>,
}

#[derive(Debug, Serialize)]
struct ProcessingStats {
    images_count: usize,
    size_saved_mb: f64,
    efficiency_percentage: f64,
}

#[derive(Debug, Deserialize)]
struct ProcessRequest {
    #[serde(flatten)]
    config: ProcessingConfig,
}

// Error handling
struct AppError(anyhow::Error);

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        error!("Application error: {:?}", self.0);
        (
            StatusCode::INTERNAL_SERVER_ERROR,
            Json(serde_json::json!({
                "error": self.0.to_string()
            })),
        )
            .into_response()
    }
}

impl<E> From<E> for AppError
where
    E: Into<anyhow::Error>,
{
    fn from(err: E) -> Self {
        Self(err.into())
    }
}

#[tokio::main]
async fn main() {
    // Initialize logging
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "image_processor_server=debug,tower_http=debug".into()),
        )
        .init();

    // Initialize libvips
    std::env::set_var("VIPS_CONCURRENCY", "4");
    let vips_app = libvips::VipsApp::new("ImageProcessor", false)
        .expect("Cannot initialize libvips");
    vips_app.concurrency_set(4);

    // Create shared state
    let state = AppState {
        jobs: Arc::new(RwLock::new(std::collections::HashMap::new())),
    };

    // Configure CORS
    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    // Build router
    let app = Router::new()
        .route("/api/health", get(health_check))
        .route("/api/process", post(process_images))
        .route("/api/job/:id", get(get_job_status))
        .route("/api/download/:id", get(download_processed))
        .nest_service("/", ServeDir::new("dist"))
        .layer(cors)
        .with_state(state);

    // Start server
    let port = std::env::var("PORT").unwrap_or_else(|_| "3000".to_string());
    let addr = format!("0.0.0.0:{}", port);
    info!("Server starting on {}", addr);

    let listener = tokio::net::TcpListener::bind(&addr)
        .await
        .expect("Failed to bind server");

    info!("Server listening on http://{}", addr);
    
    axum::serve(listener, app)
        .await
        .expect("Server error");
}

async fn health_check() -> Json<serde_json::Value> {
    Json(serde_json::json!({
        "status": "ok",
        "service": "image-processor-server"
    }))
}

async fn process_images(
    State(state): State<AppState>,
    mut multipart: Multipart,
) -> Result<Json<serde_json::Value>, AppError> {
    info!("Received image processing request");

    let job_id = Uuid::new_v4().to_string();
    let temp_dir = tempfile::tempdir()?;
    let temp_path = temp_dir.path();

    let mut config = ProcessingConfig::default();
    let mut uploaded_files = Vec::new();

    // Parse multipart form data
    while let Some(field) = multipart.next_field().await? {
        let name = field.name().unwrap_or("").to_string();
        
        if name == "config" {
            let data = field.text().await?;
            config = serde_json::from_str(&data).unwrap_or_default();
            info!("Received config: {:?}", config);
        } else if name == "files" {
            let file_name = field.file_name().unwrap_or("image").to_string();
            let data = field.bytes().await?;
            
            let input_path = temp_path.join(&file_name);
            tokio::fs::write(&input_path, &data).await?;
            info!("Uploaded file: {}", file_name);
            uploaded_files.push((file_name, input_path));
        }
    }

    let total_files = uploaded_files.len();
    
    // Initialize job status
    {
        let mut jobs = state.jobs.write().await;
        jobs.insert(
            job_id.clone(),
            JobStatus {
                id: job_id.clone(),
                total: total_files,
                processed: 0,
                status: "processing".to_string(),
                output_files: Vec::new(),
            },
        );
    }

    // Process images
    let output_dir = temp_path.join("output");
    tokio::fs::create_dir_all(&output_dir).await?;

    let job_id_clone = job_id.clone();
    let state_clone = state.clone();
    let output_dir_clone = output_dir.clone();

    tokio::spawn(async move {
        let mut processed = 0;
        let mut output_files = Vec::new();

        for (original_name, input_path) in uploaded_files {
            let input_path_str = input_path.to_str().unwrap();
            let stem = input_path.file_stem().unwrap_or_default().to_str().unwrap_or("image");
            
            // Determine output extension
            let target_ext = match config.output_format.as_deref() {
                Some("original") => {
                    input_path
                        .extension()
                        .unwrap_or_default()
                        .to_str()
                        .unwrap_or("jpg")
                }
                Some(fmt) => fmt,
                None => "jpg",
            };

            let output_name = format!("{}_processed.{}", stem, target_ext);
            let output_path = output_dir_clone.join(&output_name);
            let output_path_str = output_path.to_str().unwrap();

            match ImageProcessor::process_image(input_path_str, output_path_str, &config) {
                Ok(_) => {
                    processed += 1;
                    output_files.push(output_name);
                    info!("Successfully processed: {}", original_name);
                }
                Err(e) => {
                    error!("Failed to process {}: {:?}", original_name, e);
                }
            }

            // Update job status
            let mut jobs = state_clone.jobs.write().await;
            if let Some(job) = jobs.get_mut(&job_id_clone) {
                job.processed = processed;
                job.output_files = output_files.clone();
            }
        }

        // Mark job as complete
        let mut jobs = state_clone.jobs.write().await;
        if let Some(job) = jobs.get_mut(&job_id_clone) {
            job.status = "completed".to_string();
        }
        
        info!("Job {} completed. Processed {} files", job_id_clone, processed);
    });

    Ok(Json(serde_json::json!({
        "job_id": job_id,
        "total_files": total_files,
        "status": "processing"
    })))
}

async fn get_job_status(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
) -> Result<Json<JobStatus>, AppError> {
    let jobs = state.jobs.read().await;
    let job = jobs
        .get(&id)
        .ok_or_else(|| anyhow::anyhow!("Job not found"))?
        .clone();
    Ok(Json(job))
}

async fn download_processed(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
) -> Result<impl IntoResponse, AppError> {
    let jobs = state.jobs.read().await;
    let job = jobs
        .get(&id)
        .ok_or_else(|| anyhow::anyhow!("Job not found"))?
        .clone();

    if job.status != "completed" {
        return Err(anyhow::anyhow!("Job not yet completed").into());
    }

    // Create a zip file with all processed images
    let temp_dir = tempfile::tempdir()?;
    let zip_path = temp_dir.path().join(format!("{}.zip", id));
    let file = std::fs::File::create(&zip_path)?;
    let mut zip = zip::ZipWriter::new(file);

    // Add files to zip
    // Note: In production, you'd need to properly track and access the temp directories
    // For now, this is a placeholder structure
    
    zip.finish()?;
    drop(zip);

    let data = tokio::fs::read(&zip_path).await?;

    Ok((
        StatusCode::OK,
        [(header::CONTENT_TYPE, "application/zip")],
        data,
    ))
}
