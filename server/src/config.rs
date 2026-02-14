use std::time::Duration;

/// Server configuration loaded from environment variables
#[derive(Debug, Clone)]
pub struct ServerConfig {
    pub port: u16,
    pub vips_concurrency: usize,
    pub max_file_size_mb: usize,
    pub max_files_per_request: usize,
    pub job_ttl_minutes: u64,
    pub allowed_origins: String,
}

impl ServerConfig {
    pub fn from_env() -> Self {
        Self {
            port: std::env::var("PORT")
                .ok()
                .and_then(|p| p.parse().ok())
                .unwrap_or(3000),
            vips_concurrency: std::env::var("VIPS_CONCURRENCY")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(4),
            max_file_size_mb: std::env::var("MAX_FILE_SIZE_MB")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(50),
            max_files_per_request: std::env::var("MAX_FILES_PER_REQUEST")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(100),
            job_ttl_minutes: std::env::var("JOB_TTL_MINUTES")
                .ok()
                .and_then(|v| v.parse().ok())
                .unwrap_or(60),
            allowed_origins: std::env::var("ALLOWED_ORIGINS")
                .unwrap_or_else(|_| "http://localhost:1420,http://localhost:3000".to_string()),
        }
    }

    pub fn max_file_size_bytes(&self) -> usize {
        self.max_file_size_mb * 1024 * 1024
    }

    pub fn job_ttl(&self) -> Duration {
        Duration::from_secs(self.job_ttl_minutes * 60)
    }
}
