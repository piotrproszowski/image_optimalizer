use libvips::{ops, VipsImage};
use serde::{Deserialize, Serialize};
use std::path::Path;
use anyhow::{Result, Context};
use tracing::{info, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ProcessingConfig {
    pub max_dimension: Option<i32>,
    pub quality: Option<i32>,
    pub strip_metadata: bool,
    pub output_format: Option<String>,
    pub output_dir: Option<String>,
}

impl Default for ProcessingConfig {
    fn default() -> Self {
        Self {
            max_dimension: Some(2048),
            quality: Some(85),
            strip_metadata: true,
            output_format: Some("original".to_string()),
            output_dir: None,
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

        // Scope for VipsImage to ensure it is dropped/cleaned up
        let result = {
            let image = VipsImage::new_from_file(path).context("Failed to load image via libvips")?;
            
            // 1. Resize (Smart Thumbnailing logic if needed, or simple resize)
            let processed_image = if let Some(max_dim) = config.max_dimension {
                let width = image.get_width();
                let height = image.get_height();
                
                if width > max_dim || height > max_dim {
                    let scale = max_dim as f64 / width.max(height) as f64;
                    // libvips-rs wrappers usually take &VipsImage
                    ops::resize(&image, scale)?
                } else {
                    image
                }
            } else {
                image
            };

            // 2. Inference Placeholder (Hook for AI engine later)
            // let processed_image = engine.run(&processed_image)?;
            
            // 3. Metadata Stripping (Privacy)
            // TODO: Implement proper metadata stripping manually using image.remove() for specific fields
            // since ops::strip is not readily available in this binding version.
            let processed_image = processed_image;

            // 4. Save
            if output_path.to_lowercase().ends_with(".jpg") || output_path.to_lowercase().ends_with(".jpeg") {
                 let options = ops::JpegsaveOptions {
                    q: config.quality.unwrap_or(85),
                    ..ops::JpegsaveOptions::default()
                 };
                 ops::jpegsave_with_opts(&processed_image, output_path, &options).context("Failed to save JPG")?;
            } else if output_path.to_lowercase().ends_with(".png") {
                 let options = ops::PngsaveOptions::default();
                 ops::pngsave_with_opts(&processed_image, output_path, &options).context("Failed to save PNG")?;
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
