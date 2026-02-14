# Code Review Report

**Date:** 2026-02-14  
**Reviewer:** GitHub Copilot  
**Scope:** Web deployment conversion (server backend + frontend)

---

## Executive Summary

The web deployment conversion is **well-implemented** with a solid architecture. However, there are several **critical security and resource management issues** that should be addressed before production deployment.

**Overall Grade:** B+ (Good, with important improvements needed)

---

## Critical Issues (Must Fix)

### 🔴 1. CORS Security - SEVERITY: HIGH
**Location:** `server/src/main.rs:101-104`

```rust
let cors = CorsLayer::new()
    .allow_origin(Any)  // ⚠️ INSECURE
    .allow_methods(Any)
    .allow_headers(Any);
```

**Issue:** Allows requests from any origin, making the API vulnerable to CSRF attacks.

**Recommendation:**
```rust
let cors = CorsLayer::new()
    .allow_origin(
        std::env::var("ALLOWED_ORIGINS")
            .unwrap_or_else(|_| "http://localhost:1420,http://localhost:3000".to_string())
            .parse::<HeaderValue>()
            .unwrap()
    )
    .allow_methods([Method::GET, Method::POST])
    .allow_headers([header::CONTENT_TYPE, header::AUTHORIZATION]);
```

---

### 🔴 2. Memory Leak - Temp Directory Storage - SEVERITY: HIGH
**Location:** `server/src/main.rs:26-28`

```rust
struct AppState {
    jobs: Arc<RwLock<std::collections::HashMap<String, JobStatus>>>,
    temp_dirs: Arc<RwLock<std::collections::HashMap<String, String>>>,  // ⚠️ Never cleaned
}
```

**Issue:** Job data and temp directories accumulate indefinitely in memory. Over time, this will cause memory exhaustion.

**Recommendation:**
- Implement TTL-based cleanup (e.g., remove jobs older than 1 hour)
- Add background task to clean old jobs and temp directories
- Consider using a proper job queue system (e.g., Redis) for production

```rust
// Add cleanup task in main()
tokio::spawn(cleanup_old_jobs(state.clone()));

async fn cleanup_old_jobs(state: AppState) {
    loop {
        tokio::time::sleep(Duration::from_secs(300)).await; // Every 5 minutes
        // Remove jobs older than 1 hour
        // Clean up temp directories
    }
}
```

---

### 🔴 3. Temporary Directory Lifecycle Issue - SEVERITY: HIGH
**Location:** `server/src/main.rs:146-147`

```rust
let temp_dir = tempfile::tempdir()?;
let temp_path = temp_dir.path();
```

**Issue:** `temp_dir` is dropped at the end of `process_images()`, which deletes the directory. But the processing happens in `tokio::spawn()` (line 202) which continues AFTER the function returns. This means files will be deleted while processing is still happening.

**Recommendation:**
```rust
let temp_dir = tempfile::tempdir()?;
let temp_path = temp_dir.path().to_path_buf();
let temp_dir = Arc::new(Mutex::new(Some(temp_dir))); // Keep alive

// In tokio::spawn, store the temp_dir Arc
tokio::spawn(async move {
    let _temp_dir_guard = temp_dir; // Keep alive until processing completes
    // ... processing ...
});
```

---

### 🟡 4. No File Upload Validation - SEVERITY: MEDIUM
**Location:** `server/src/main.rs:160-168`

**Issues:**
- No file size limit (DoS vulnerability)
- No file type validation
- No maximum number of files limit
- Malicious filenames not sanitized

**Recommendation:**
```rust
const MAX_FILE_SIZE: usize = 50 * 1024 * 1024; // 50MB
const MAX_FILES: usize = 100;

// In process_images:
if data.len() > MAX_FILE_SIZE {
    return Err(anyhow::anyhow!("File too large").into());
}
if uploaded_files.len() >= MAX_FILES {
    return Err(anyhow::anyhow!("Too many files").into());
}

// Sanitize filename
let safe_filename = sanitize_filename(&file_name);
```

---

### 🟡 5. Synchronous I/O in Async Context - SEVERITY: MEDIUM
**Location:** `server/src/main.rs:300-313`

```rust
let file = std::fs::File::create(&zip_path)?;  // ⚠️ Blocking
let mut zip = zip::ZipWriter::new(file);
// ...
let file_data = std::fs::read(&file_path)?;  // ⚠️ Blocking
```

**Issue:** Blocking file I/O in async function can cause thread starvation.

**Recommendation:**
```rust
// Use tokio::task::spawn_blocking for sync I/O
let zip_data = tokio::task::spawn_blocking(move || {
    let file = std::fs::File::create(&zip_path)?;
    let mut zip = zip::ZipWriter::new(file);
    // ... zip creation ...
    Ok::<Vec<u8>, anyhow::Error>(data)
}).await??;
```

---

### 🟡 6. Unwrap Usage - SEVERITY: MEDIUM
**Locations:** Multiple

```rust
line 207: input_path.to_str().unwrap()
line 225: output_path.to_str().unwrap()
line 161: field.file_name().unwrap_or("image")
```

**Issue:** Can panic if paths contain invalid UTF-8.

**Recommendation:** Use proper error handling:
```rust
let input_path_str = input_path.to_str()
    .ok_or_else(|| anyhow::anyhow!("Invalid path encoding"))?;
```

---

## Important Issues (Should Fix)

### 🟢 7. Dead Code - Unused Structs
**Location:** `server/src/main.rs:40-51`

```rust
#[derive(Debug, Serialize)]
struct ProcessingStats { ... }  // ⚠️ Never used

#[derive(Debug, Deserialize)]
struct ProcessRequest { ... }  // ⚠️ Never used
```

**Recommendation:** Remove if not needed, or implement usage.

---

### 🟢 8. Missing Rate Limiting
**Issue:** No protection against abuse - single client can spam the server.

**Recommendation:** Add rate limiting middleware:
```rust
use tower::ServiceBuilder;
use tower_http::limit::RequestBodyLimitLayer;

let app = Router::new()
    // ...
    .layer(
        ServiceBuilder::new()
            .layer(RequestBodyLimitLayer::new(100 * 1024 * 1024)) // 100MB max
            .layer(/* rate limiting */)
    );
```

---

### 🟢 9. No Health Check for Dependencies
**Location:** `server/src/main.rs:132-137`

**Issue:** Health check doesn't verify libvips or file system availability.

**Recommendation:**
```rust
async fn health_check(State(state): State<AppState>) -> Json<serde_json::Value> {
    let libvips_ok = check_libvips_available();
    let disk_ok = check_disk_space();
    
    Json(serde_json::json!({
        "status": if libvips_ok && disk_ok { "ok" } else { "degraded" },
        "service": "image-processor-server",
        "checks": {
            "libvips": libvips_ok,
            "disk": disk_ok
        }
    }))
}
```

---

### 🟢 10. Missing Logging for Security Events
**Recommendation:** Add structured logging for:
- Failed authentication attempts (when auth is added)
- Large file uploads
- Processing errors
- Job completions

---

## Code Quality Issues

### 11. Code Duplication
**Location:** `server/src/processing.rs` vs `src-tauri/src/processing.rs`

The image processing logic is duplicated. Consider:
- Extracting to a shared crate
- Or documenting synchronization strategy

---

### 12. Missing Documentation
**Issues:**
- No doc comments on public functions
- No module-level documentation
- No API documentation beyond DEPLOYMENT.md

**Recommendation:** Add rustdoc comments:
```rust
/// Process images uploaded via multipart form
/// 
/// # Arguments
/// * `state` - Application state containing job tracking
/// * `multipart` - Multipart form data with config and files
/// 
/// # Returns
/// Job ID and initial status
async fn process_images(...) -> Result<...> {
```

---

### 13. Configuration Hardcoding
**Issues:**
- VIPS_CONCURRENCY=4 hardcoded
- Port default hardcoded
- No request timeout configuration

**Recommendation:** Use config struct:
```rust
#[derive(Debug)]
struct ServerConfig {
    port: u16,
    vips_concurrency: usize,
    max_file_size: usize,
    job_ttl: Duration,
}

impl ServerConfig {
    fn from_env() -> Result<Self> {
        // Load from environment
    }
}
```

---

## Testing Issues

### 14. No Tests
**Critical Gap:** Zero test coverage for new server code.

**Recommendation:** Add tests:
```rust
#[cfg(test)]
mod tests {
    use super::*;
    
    #[tokio::test]
    async fn test_health_check() { ... }
    
    #[tokio::test]
    async fn test_process_images() { ... }
    
    #[tokio::test]
    async fn test_invalid_file_rejected() { ... }
}
```

---

## Frontend Issues (App-web.tsx)

### 15. No Upload Progress Indicator
**Location:** `src/App-web.tsx:363-380`

Users don't see upload progress for large files.

**Recommendation:** Use XMLHttpRequest or fetch with progress events.

---

### 16. Polling Interval Not Configurable
**Location:** `src/App-web.tsx:308`

```javascript
}, 1000);  // Hardcoded 1 second
```

**Recommendation:** Use exponential backoff:
```javascript
const interval = Math.min(10000, 1000 * Math.pow(1.5, pollCount));
```

---

### 17. No Error Retry Logic
If polling fails, it just stops. Should retry with backoff.

---

## Docker Issues

### 18. No Health Check in Dockerfile
**Recommendation:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:3000/api/health || exit 1
```

---

### 19. Running as Root
**Security Issue:** Container runs as root user.

**Recommendation:**
```dockerfile
RUN useradd -m -u 1000 appuser
USER appuser
```

---

## Positive Observations ✅

1. **Clean Architecture:** Clear separation of concerns
2. **Good Error Handling Pattern:** Custom AppError type
3. **Proper Async Usage:** Mostly correct tokio usage
4. **Type Safety:** Strong typing throughout
5. **Documentation:** Excellent deployment documentation
6. **Docker Multi-stage:** Efficient container builds
7. **Resource Management:** Uses Arc/RwLock appropriately (except cleanup issue)

---

## Priority Recommendations

### Must Fix Before Production:
1. ✅ Fix CORS security
2. ✅ Implement job cleanup / TTL
3. ✅ Fix temp directory lifecycle
4. ✅ Add file upload validation
5. ✅ Add rate limiting

### Should Fix Soon:
6. ✅ Fix blocking I/O in async
7. ✅ Remove unwrap() calls
8. ✅ Add health check improvements
9. ✅ Add basic tests
10. ✅ Run as non-root in Docker

### Nice to Have:
11. ✅ Add comprehensive documentation
12. ✅ Improve frontend error handling
13. ✅ Add monitoring/metrics
14. ✅ Implement shared processing crate

---

## Security Checklist

- [ ] CORS properly configured
- [ ] File upload limits enforced
- [ ] Input validation on all endpoints
- [ ] Rate limiting implemented
- [ ] Secrets not in code
- [ ] Container runs as non-root
- [ ] Dependencies regularly updated
- [ ] Logging includes security events

---

## Conclusion

The implementation demonstrates **solid engineering fundamentals** with clean architecture and good practices. However, **security and resource management issues must be addressed** before production use.

**Estimated effort to address critical issues:** 2-3 days

**Recommended next steps:**
1. Address critical security issues (CORS, file validation)
2. Implement job cleanup mechanism
3. Add basic test coverage
4. Conduct security audit before production deployment

---

*This review was generated on 2026-02-14. Code may have changed since then.*
