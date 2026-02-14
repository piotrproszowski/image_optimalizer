use libvips::{ops, VipsImage};
use serde::{Deserialize, Serialize};
use std::path::Path;
use anyhow::{Result, Context};
use tracing::info;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProcessingConfig {
    pub max_dimension: Option<i32>,
    pub quality: Option<i32>,
    pub strip_metadata: bool,
    pub output_format: Option<String>,
}

impl Default for ProcessingConfig {
    fn default() -> Self {
        Self {
            max_dimension: Some(2048),
            quality: Some(85),
            strip_metadata: true,
            output_format: Some("original".to_string()),
        }
    }
}

pub struct ImageProcessor;

impl ImageProcessor {
    pub fn process_image(path: &str, output_path: &str, config: &ProcessingConfig) -> Result<()> {
        let path_obj = Path::new(path);
        if !path_obj.exists() {
            anyhow::bail!("File not found: {}", path);
        }

        let input_ext = path_obj.extension().and_then(|e| e.to_str()).map(|e| e.to_lowercase());
        let output_ext = Path::new(output_path)
            .extension()
            .and_then(|e| e.to_str())
            .map(|e| e.to_lowercase());

        // Scope for VipsImage to ensure it is dropped/cleaned up
        let result = {
            let image = VipsImage::new_from_file(path).context("Failed to load image via libvips")?;
            
            // 1. Resize (Smart Thumbnailing logic if needed, or simple resize)
            let processed_image = if let Some(max_dim) = config.max_dimension {
                let width = image.get_width();
                let height = image.get_height();
                
                if width > max_dim || height > max_dim {
                    let scale = max_dim as f64 / width.max(height) as f64;
                    ops::resize(&image, scale)?
                } else {
                    image
                }
            } else {
                image
            };

            // 2. Metadata Stripping (Privacy)
            let processed_image = processed_image;

            // 3. Save
            if output_path.to_lowercase().ends_with(".jpg") || output_path.to_lowercase().ends_with(".jpeg") {
                let mut quality = config.quality.unwrap_or(85).clamp(1, 100);
                let save_jpeg = |img: &VipsImage, path: &str, q: i32| -> Result<()> {
                    let options = ops::JpegsaveOptions {
                        q,
                        ..ops::JpegsaveOptions::default()
                    };
                    ops::jpegsave_with_opts(img, path, &options).context("Failed to save JPG")?;
                    Ok(())
                };
                save_jpeg(&processed_image, output_path, quality)?;

                if matches!(input_ext.as_deref(), Some("jpg") | Some("jpeg"))
                    && matches!(output_ext.as_deref(), Some("jpg") | Some("jpeg"))
                {
                    let input_size = std::fs::metadata(path).context("Failed to read input size")?.len();
                    let mut output_size = std::fs::metadata(output_path).context("Failed to read output size")?.len();
                    while output_size >= input_size && quality > 30 {
                        quality = (quality - 5).max(30);
                        save_jpeg(&processed_image, output_path, quality)?;
                        output_size = std::fs::metadata(output_path).context("Failed to read output size")?.len();
                    }
                    if output_size >= input_size {
                        anyhow::bail!("JPEG output larger than input after compression");
                    }
                }
            } else if output_path.to_lowercase().ends_with(".png") {
                let options = ops::PngsaveOptions::default();
                ops::pngsave_with_opts(&processed_image, output_path, &options).context("Failed to save PNG")?;
            } else if output_path.to_lowercase().ends_with(".avif") {
                let quality = config.quality.unwrap_or(85).clamp(1, 100);
                processed_image
                    .image_write_to_file(&format!("{}[Q={}]", output_path, quality))
                    .context("Failed to save AVIF")?;
            } else if output_path.to_lowercase().ends_with(".webp") {
                let options = ops::WebpsaveOptions {
                    q: config.quality.unwrap_or(85),
                    ..ops::WebpsaveOptions::default()
                };
                ops::webpsave_with_opts(&processed_image, output_path, &options).context("Failed to save WebP")?;
            } else {
                // Fallback
                processed_image.image_write_to_file(output_path).context("Failed to generic save")?;
            }
            
            info!("Processed: {} -> {}", path, output_path);
            Ok::<(), anyhow::Error>(())
        };

        result
    }
}
