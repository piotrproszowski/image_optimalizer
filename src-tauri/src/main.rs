use mimalloc::MiMalloc;

#[global_allocator]
static GLOBAL: MiMalloc = MiMalloc;

use image_processor_lib::run;

fn main() {
    // Initialize logging
    tracing_subscriber::fmt::init();

    // Critical: Set VIPS concurrency before initialization
    std::env::set_var("VIPS_CONCURRENCY", "4");

    // Initialize libvips
    let vips_app = libvips::VipsApp::new("ImageOptimizer", false)
        .expect("Cannot initialize libvips");
    
    // Set Vips cache limit (100MB) to prevent memory ballooning
    vips_app.concurrency_set(4);
    // Note: libvips-rs might not expose cache_set_max directly on the App struct in older versions
    // but the environment variable VIPS_DISC_THRESHOLD acts similarly or we use unsafe
    // For now, reliance on VIPS_CONCURRENCY and standard GC is step 1.

    run();
}
