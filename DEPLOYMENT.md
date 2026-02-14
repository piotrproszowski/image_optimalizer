# Image Processor - Web Deployment Guide

## Overview

The Image Processor has been refactored to support both desktop (Tauri) and web deployment modes. This guide covers the web deployment setup.

## Architecture

### Web Mode
- **Frontend**: React + TypeScript + Vite (Static files)
- **Backend**: Rust web server using Axum framework
- **Image Processing**: libvips library
- **Deployment**: Docker containerization

### Components

1. **Server** (`/server`): Rust web server with HTTP API
   - File upload handling (multipart/form-data)
   - Image processing using libvips
   - Job status tracking
   - Processed file download

2. **Frontend** (`/src/App-web.tsx`): Web-optimized React UI
   - File upload via drag-and-drop or file picker
   - Progress tracking via polling
   - Download processed images

## Local Development

### Prerequisites

```bash
# Install libvips
# macOS
brew install vips

# Ubuntu/Debian
sudo apt-get install libvips-dev

# Install Node.js dependencies
npm install
```

### Running Locally

**Option 1: Separate processes**

Terminal 1 - Start backend server:
```bash
npm run server:dev
# Or directly:
cd server && cargo run
```

Terminal 2 - Start frontend dev server:
```bash
npm run dev:web
```

Access: http://localhost:1420

**Option 2: Production build**

```bash
# Build frontend
npm run build:web

# Build server
npm run server:build

# Run server (serves both API and static files)
cd server && ./target/release/image-processor-server
```

Access: http://localhost:3000

## Docker Deployment

### Build and Run

```bash
# Build Docker image
docker build -t image-processor:latest .

# Run container
docker run -p 3000:3000 image-processor:latest

# Or use docker-compose
docker-compose up -d
```

### Docker Compose

The `docker-compose.yml` file provides:
- Automatic restart
- Health checks
- Volume mounting for persistent data
- Environment configuration

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## Environment Variables

### Frontend (.env.web, .env.production)
```bash
VITE_API_URL=http://localhost:3000  # Backend API URL
VITE_MODE=web                        # Deployment mode
```

### Backend
```bash
PORT=3000                # Server port
RUST_LOG=info           # Log level
VIPS_CONCURRENCY=4      # libvips thread count
```

## API Endpoints

### Health Check
```
GET /api/health
Response: { "status": "ok", "service": "image-processor-server" }
```

### Process Images
```
POST /api/process
Content-Type: multipart/form-data

Fields:
- config: JSON string with processing configuration
- files: One or more image files

Response: { "job_id": "uuid", "total_files": 5, "status": "processing" }
```

### Job Status
```
GET /api/job/:id
Response: {
  "id": "uuid",
  "total": 5,
  "processed": 3,
  "status": "processing",
  "output_files": ["file1.webp", "file2.webp"]
}
```

### Download Results
```
GET /api/download/:id
Response: ZIP file with processed images
```

## Server Deployment

### Option 1: VPS/Cloud Server

1. Install dependencies:
```bash
sudo apt-get update
sudo apt-get install -y libvips42 libglib2.0-0
```

2. Copy binary and dist folder:
```bash
scp -r server/target/release/image-processor-server user@server:/app/
scp -r dist user@server:/app/
```

3. Run with systemd service:

Create `/etc/systemd/system/image-processor.service`:
```ini
[Unit]
Description=Image Processor Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/app
ExecStart=/app/image-processor-server
Restart=always
Environment="PORT=3000"
Environment="RUST_LOG=info"

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable image-processor
sudo systemctl start image-processor
```

### Option 2: Docker on Server

```bash
# Upload files
scp -r . user@server:/app/image-processor/

# SSH to server
ssh user@server

# Build and run
cd /app/image-processor
docker-compose up -d
```

### Option 3: Cloud Platforms

**Heroku:**
- Use `heroku.yml` or Dockerfile
- Set buildpack for Rust
- Configure environment variables

**DigitalOcean App Platform:**
- Connect GitHub repository
- Select Dockerfile deployment
- Configure port and environment

**AWS ECS/Fargate:**
- Push Docker image to ECR
- Create task definition
- Deploy service

## Nginx Reverse Proxy

For production, use Nginx as reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    client_max_body_size 100M;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## Performance Tuning

### libvips Configuration
```bash
export VIPS_CONCURRENCY=4        # Number of threads
export VIPS_DISC_THRESHOLD=100m  # Memory threshold before disk cache
```

### Server Configuration
- Adjust worker threads in Axum
- Configure max upload size
- Set appropriate timeout values

## Monitoring

### Health Checks
```bash
curl http://localhost:3000/api/health
```

### Logs
```bash
# Docker
docker-compose logs -f

# Systemd
sudo journalctl -u image-processor -f
```

## Troubleshooting

### libvips not found
```bash
# Check installation
vips --version
pkg-config --libs vips

# Set library path if needed
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

### CORS issues
- Configure CORS in server/src/main.rs
- Update allowed origins for production

### Upload size limits
- Adjust `client_max_body_size` in Nginx
- Configure Axum's multipart limits

## Security Considerations

1. **File Upload Validation**
   - Validate file types and sizes
   - Scan for malicious content
   - Limit upload rate

2. **Resource Limits**
   - Set max concurrent jobs
   - Implement request rate limiting
   - Configure memory limits

3. **HTTPS**
   - Use Let's Encrypt certificates
   - Configure SSL in Nginx or load balancer

4. **Authentication** (if needed)
   - Add JWT or session-based auth
   - Implement API keys for service access

## Migration from Desktop

The application now supports both modes:

- **Desktop mode**: Original Tauri-based application
  - Run: `npm run tauri dev`
  - Build: `npm run tauri build`

- **Web mode**: New web-accessible deployment
  - Run: `npm run dev:web` + `npm run server:dev`
  - Build: `npm run build:web` + `npm run server:build`

Both modes share the same core image processing logic, ensuring consistent results.
