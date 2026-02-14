use axum::{
    extract::{Multipart, Path as AxumPath, State},
    http::{header, HeaderMap, HeaderValue, Method, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use std::time::{Duration, SystemTime};
use tokio::sync::{Mutex, RwLock};
use tower_http::cors::CorsLayer;
use tower_http::services::ServeDir;
use tracing::{error, info, warn};
use uuid::Uuid;

mod config;
mod processing;
use config::ServerConfig;
use processing::{ImageProcessor, ProcessingConfig};

use mimalloc::MiMalloc;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

// State structures
#[derive(Clone)]
struct AppState {
    jobs: Arc<RwLock<std::collections::HashMap<String, JobInfo>>>,
    config: Arc<ServerConfig>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct JobStatus {
    id: String,
    total: usize,
    processed: usize,
    status: String,
    output_files: Vec<String>,
}

#[derive(Debug, Clone)]
struct JobInfo {
    status: JobStatus,
    temp_dir: Arc<Mutex<Option<tempfile::TempDir>>>,
    created_at: SystemTime,
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

    // Load configuration
    let config = Arc::new(ServerConfig::from_env());
    info!("Server configuration loaded: {:?}", config);

    // Initialize libvips
    std::env::set_var("VIPS_CONCURRENCY", config.vips_concurrency.to_string());
    let vips_app = libvips::VipsApp::new("ImageProcessor", false)
        .expect("Cannot initialize libvips");
    vips_app.concurrency_set(config.vips_concurrency as i32);

    // Create shared state
    let state = AppState {
        jobs: Arc::new(RwLock::new(std::collections::HashMap::new())),
        config: config.clone(),
    };

    // Start cleanup task
    tokio::spawn(cleanup_old_jobs(state.clone()));

    // Configure CORS with specific origins
    let allowed_origins: Vec<HeaderValue> = config
        .allowed_origins
        .split(',')
        .filter_map(|origin| origin.trim().parse().ok())
        .collect();
    
    let cors = CorsLayer::new()
        .allow_origin(allowed_origins)
        .allow_methods([Method::GET, Method::POST])
        .allow_headers([header::CONTENT_TYPE, header::AUTHORIZATION]);

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
    let addr = format!("0.0.0.0:{}", config.port);
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

/// Background task to clean up old jobs
async fn cleanup_old_jobs(state: AppState) {
    loop {
        tokio::time::sleep(Duration::from_secs(300)).await; // Every 5 minutes
        
        let mut jobs = state.jobs.write().await;
        let now = SystemTime::now();
        let ttl = state.config.job_ttl();
        
        let mut to_remove = Vec::new();
        for (id, job_info) in jobs.iter() {
            if let Ok(elapsed) = now.duration_since(job_info.created_at) {
                if elapsed > ttl {
                    to_remove.push(id.clone());
                }
            }
        }
        
        for id in to_remove {
            if let Some(job_info) = jobs.remove(&id) {
                info!("Cleaned up old job: {}", id);
                // Temp directory will be automatically cleaned up when Arc is dropped
                drop(job_info.temp_dir);
            }
        }
    }
}

/// Sanitize filename to prevent path traversal attacks
fn sanitize_filename(filename: &str) -> String {
    filename
        .chars()
        .filter(|c| c.is_alphanumeric() || *c == '.' || *c == '-' || *c == '_')
        .take(255)
        .collect()
}

/// Validate file extension
fn is_valid_image_extension(filename: &str) -> bool {
    let valid_extensions = ["jpg", "jpeg", "png", "webp", "heic", "avif", "tiff", "gif"];
    filename
        .split('.')
        .last()
        .map(|ext| valid_extensions.contains(&ext.to_lowercase().as_str()))
        .unwrap_or(false)
}

async fn process_images(
    State(state): State<AppState>,
    mut multipart: Multipart,
) -> Result<Json<serde_json::Value>, AppError> {
    info!("Received image processing request");

    let job_id = Uuid::new_v4().to_string();
    let temp_dir = tempfile::tempdir()?;
    let temp_path = temp_dir.path().to_path_buf();
    let temp_dir_arc = Arc::new(Mutex::new(Some(temp_dir)));

    let mut config = ProcessingConfig::default();
    let mut uploaded_files = Vec::new();
    
    let max_file_size = state.config.max_file_size_bytes();
    let max_files = state.config.max_files_per_request;

    // Parse multipart form data
    while let Some(field) = multipart.next_field().await? {
        let name = field.name().unwrap_or("").to_string();
        
        if name == "config" {
            let data = field.text().await?;
            config = serde_json::from_str(&data).unwrap_or_default();
            info!("Received config: {:?}", config);
        } else if name == "files" {
            // Check file count limit
            if uploaded_files.len() >= max_files {
                return Err(anyhow::anyhow!(
                    "Too many files. Maximum {} files allowed per request",
                    max_files
                )
                .into());
            }

            let file_name = field.file_name().unwrap_or("image").to_string();
            
            // Validate file extension
            if !is_valid_image_extension(&file_name) {
                warn!("Rejected file with invalid extension: {}", file_name);
                return Err(anyhow::anyhow!("Invalid file type: {}", file_name).into());
            }
            
            // Sanitize filename
            let safe_filename = sanitize_filename(&file_name);
            if safe_filename.is_empty() {
                return Err(anyhow::anyhow!("Invalid filename").into());
            }
            
            let data = field.bytes().await?;
            
            // Check file size
            if data.len() > max_file_size {
                return Err(anyhow::anyhow!(
                    "File {} too large. Maximum size is {} MB",
                    safe_filename,
                    state.config.max_file_size_mb
                )
                .into());
            }
            
            let input_path = temp_path.join(&safe_filename);
            tokio::fs::write(&input_path, &data).await?;
            info!("Uploaded file: {} ({} bytes)", safe_filename, data.len());
            uploaded_files.push((safe_filename, input_path));
        }
    }

    let total_files = uploaded_files.len();
    
    if total_files == 0 {
        return Err(anyhow::anyhow!("No files uploaded").into());
    }
    
    // Initialize job status
    let job_info = JobInfo {
        status: JobStatus {
            id: job_id.clone(),
            total: total_files,
            processed: 0,
            status: "processing".to_string(),
            output_files: Vec::new(),
        },
        temp_dir: temp_dir_arc.clone(),
        created_at: SystemTime::now(),
    };
    
    {
        let mut jobs = state.jobs.write().await;
        jobs.insert(job_id.clone(), job_info);
    }

    // Process images
    let output_dir = temp_path.join("output");
    tokio::fs::create_dir_all(&output_dir).await?;

    let job_id_clone = job_id.clone();
    let state_clone = state.clone();
    let output_dir_clone = output_dir.clone();
    let temp_dir_guard = temp_dir_arc.clone();

    tokio::spawn(async move {
        let _temp_guard = temp_dir_guard; // Keep temp_dir alive
        let mut processed = 0;
        let mut output_files = Vec::new();

        for (original_name, input_path) in uploaded_files {
            let input_path_str = match input_path.to_str() {
                Some(s) => s,
                None => {
                    error!("Invalid path encoding for: {:?}", input_path);
                    continue;
                }
            };
            
            let stem = input_path
                .file_stem()
                .and_then(|s| s.to_str())
                .unwrap_or("image");
            
            // Determine output extension
            let target_ext = match config.output_format.as_deref() {
                Some("original") => {
                    input_path
                        .extension()
                        .and_then(|e| e.to_str())
                        .unwrap_or("jpg")
                }
                Some(fmt) => fmt,
                None => "jpg",
            };

            let output_name = format!("{}_processed.{}", stem, target_ext);
            let output_path = output_dir_clone.join(&output_name);
            let output_path_str = match output_path.to_str() {
                Some(s) => s,
                None => {
                    error!("Invalid output path encoding");
                    continue;
                }
            };

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
            if let Some(job_info) = jobs.get_mut(&job_id_clone) {
                job_info.status.processed = processed;
                job_info.status.output_files = output_files.clone();
            }
        }

        // Mark job as complete
        let mut jobs = state_clone.jobs.write().await;
        if let Some(job_info) = jobs.get_mut(&job_id_clone) {
            job_info.status.status = "completed".to_string();
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
    let job_info = jobs
        .get(&id)
        .ok_or_else(|| anyhow::anyhow!("Job not found"))?;
    Ok(Json(job_info.status.clone()))
}

async fn download_processed(
    State(state): State<AppState>,
    AxumPath(id): AxumPath<String>,
) -> Result<impl IntoResponse, AppError> {
    let jobs = state.jobs.read().await;
    let job_info = jobs
        .get(&id)
        .ok_or_else(|| anyhow::anyhow!("Job not found"))?
        .clone();
    drop(jobs);

    if job_info.status.status != "completed" {
        return Err(anyhow::anyhow!("Job not yet completed").into());
    }

    // Get temp directory from the Arc
    let temp_dir_guard = job_info.temp_dir.lock().await;
    let temp_path = temp_dir_guard
        .as_ref()
        .ok_or_else(|| anyhow::anyhow!("Temp directory already cleaned up"))?
        .path()
        .to_path_buf();
    drop(temp_dir_guard);

    let output_dir = temp_path.join("output");

    // Create ZIP file in a blocking task to avoid blocking async executor
    let job_files = job_info.status.output_files.clone();
    let id_clone = id.clone();
    let zip_data = tokio::task::spawn_blocking(move || -> Result<Vec<u8>, anyhow::Error> {
        let zip_temp_dir = tempfile::tempdir()?;
        let zip_path = zip_temp_dir.path().join(format!("{}.zip", id_clone));
        let file = std::fs::File::create(&zip_path)?;
        let mut zip = zip::ZipWriter::new(file);

        let options = zip::write::FileOptions::default()
            .compression_method(zip::CompressionMethod::Stored)
            .unix_permissions(0o644);

        // Add all output files to zip
        for output_file in &job_files {
            let file_path = output_dir.join(output_file);
            if file_path.exists() {
                let file_data = std::fs::read(&file_path)?;
                zip.start_file(output_file, options)?;
                std::io::Write::write_all(&mut zip, &file_data)?;
            }
        }

        zip.finish()?;
        
        // Read the zip file
        let data = std::fs::read(&zip_path)?;
        Ok(data)
    })
    .await??;
    
    let mut headers = HeaderMap::new();
    headers.insert(header::CONTENT_TYPE, HeaderValue::from_static("application/zip"));
    headers.insert(
        header::CONTENT_DISPOSITION,
        HeaderValue::from_str(&format!("attachment; filename=\"processed-images-{}.zip\"", id))
            .unwrap_or_else(|_| HeaderValue::from_static("attachment; filename=\"processed-images.zip\"")),
    );

    Ok((StatusCode::OK, headers, zip_data))
}
