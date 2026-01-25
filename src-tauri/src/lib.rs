use tauri::{Emitter, Manager, Window};
use tokio::sync::Semaphore;
use std::sync::Arc;
use serde::Serialize;
use anyhow::Context;

mod processing;
mod inference;

use processing::{ProcessingConfig, ImageProcessor};

#[derive(Serialize, Clone)]
struct ProcessingStats {
    images_count: usize,
    size_saved_mb: f64,
    efficiency_percentage: f64,
}

#[derive(Serialize, Clone)]
struct ProgressUpdate {
    current: usize,
    total: usize,
    last_file: String,
    status: String,
}

#[tauri::command]
async fn process_images(files: Vec<String>, config: ProcessingConfig, window: Window) -> Result<ProcessingStats, String> {
    tracing::info!("Received batch of {} paths with config: {:?}", files.len(), config);
    
    // Expand directories to files
    let mut all_files = Vec::new();
    for path_str in files {
        let path = std::path::Path::new(&path_str);
        if path.is_dir() {
            tracing::info!("Scanning directory: {}", path_str);
            for entry in walkdir::WalkDir::new(path).into_iter().filter_map(|e| e.ok()) {
                if entry.file_type().is_file() {
                    let p = entry.path();
                    if let Some(ext) = p.extension().and_then(|e| e.to_str()) {
                        let ext = ext.to_lowercase();
                        if matches!(ext.as_str(), "jpg" | "jpeg" | "png" | "webp" | "heic" | "avif" | "tiff") {
                            all_files.push(p.to_string_lossy().to_string());
                        }
                    }
                }
            }
        } else {
            all_files.push(path_str);
        }
    }

    let total_files = all_files.len();
    tracing::info!("Total files to process after expansion: {}", total_files);
    
    // Concurrency Limiter (e.g., 4 threads for Vips based on our Env Var)
    let semaphore = Arc::new(Semaphore::new(4));
    
    let mut success_count = 0;
    let mut total_saved_mb = 0.0;

    for (i, file_path) in all_files.iter().enumerate() {
        let permit = semaphore.clone().acquire_owned().await.unwrap();
        let file_path = file_path.clone();
        let config = config.clone();
        let window = window.clone();
        
        let _ = window.emit("progress_update", ProgressUpdate {
            current: i + 1,
            total: total_files,
            last_file: file_path.clone(),
            status: "Processing".to_string(),
        });

        let file_path_for_log = file_path.clone();

        let result = tokio::task::spawn_blocking(move || {
            let _permit = permit;
            
            let path_obj = std::path::Path::new(&file_path);
            let stem = path_obj.file_stem().unwrap_or_default().to_str().unwrap_or("image");

            // Determine extension based on config
            let target_ext = match config.output_format.as_deref() {
                Some("original") => path_obj.extension().unwrap_or_default().to_str().unwrap_or("jpg"),
                Some(fmt) => fmt,
                None => "jpg" // Fallback
            };

            // Determine output directory
            let output_dir_buf; // Keep buffer alive
            let parent = if let Some(custom_dir) = &config.output_dir {
                 output_dir_buf = std::path::PathBuf::from(custom_dir);
                 // If not absolute, might be relative to app? Assume user gave absolute path from dialog.
                 &output_dir_buf
            } else {
                 path_obj.parent().unwrap_or(std::path::Path::new("."))
            };
            
            // Ensure output dir exists
            if !parent.exists() {
                let _ = std::fs::create_dir_all(parent);
            }

            let output_path = parent.join(format!("{}_processed.{}", stem, target_ext));
            
            ImageProcessor::process_image(&file_path, output_path.to_str().unwrap(), &config)
        }).await;

        match result {
            Ok(Ok(_)) => {
                success_count += 1;
                total_saved_mb += 1.5; // Dummy logic. Real logic needs file size diff.
            },
            Ok(Err(e)) => {
                tracing::error!("Failed to process {}: {:?}", file_path_for_log, e);
            },
            Err(e) => {
                tracing::error!("Task panic for {}: {:?}", file_path_for_log, e);
            }
        }
    }

    Ok(ProcessingStats {
        images_count: success_count,
        size_saved_mb: total_saved_mb,
        efficiency_percentage: if total_files > 0 { (success_count as f64 / total_files as f64) * 100.0 } else { 0.0 },
    })
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![process_images])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
