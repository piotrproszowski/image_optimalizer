fn main() {
  // Fix for macOS ARM: Ensure linker finds Homebrew libraries
  #[cfg(target_os = "macos")]
  println!("cargo:rustc-link-search=native=/opt/homebrew/lib");

  tauri_build::build();
}
