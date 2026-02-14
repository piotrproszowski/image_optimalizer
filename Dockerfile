# Multi-stage build for web deployment
FROM rust:1.77-slim as rust-builder

# Install dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libvips-dev \
    libglib2.0-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy server code
COPY server/ ./server/

# Build server
WORKDIR /app/server
RUN cargo build --release

# Frontend build stage
FROM node:20-slim as frontend-builder

WORKDIR /app

# Copy frontend code
COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY tailwind.config.js ./
COPY postcss.config.js ./
COPY components.json ./
COPY index.html ./
COPY src/ ./src/
COPY public/ ./public/

# Install dependencies and build
RUN npm ci
RUN npm run build:web

# Final stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libvips42 \
    libglib2.0-0 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy server binary
COPY --from=rust-builder /app/server/target/release/image-processor-server /app/server

# Copy frontend build
COPY --from=frontend-builder /app/dist /app/dist

# Environment variables
ENV PORT=3000
ENV RUST_LOG=info
ENV VIPS_CONCURRENCY=4

# Expose port
EXPOSE 3000

# Run server
CMD ["/app/server"]
