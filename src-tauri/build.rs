fn main() {
  // Fix for macOS ARM: Ensure linker finds Homebrew libraries
  #[cfg(target_os = "macos")]
  {
    let homebrew_prefix = std::process::Command::new("brew")
      .arg("--prefix")
      .output()
      .map(|o| String::from_utf8_lossy(&o.stdout).trim().to_string())
      .unwrap_or_else(|_| "/usr/local".to_string());
    println!("cargo:rustc-link-search=native={}/lib", homebrew_prefix);
  }

  tauri_build::build();
}
