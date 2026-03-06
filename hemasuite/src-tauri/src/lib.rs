use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::Manager;

struct SidecarState(Mutex<Option<Child>>);

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(SidecarState(Mutex::new(None)))
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .setup(|app| {
            let sidecar_dir = app
                .path()
                .resource_dir()
                .unwrap_or_default()
                .join("sidecar");

            // In dev mode, use the sidecar directory relative to src-tauri
            let working_dir = if sidecar_dir.join("server.py").exists() {
                sidecar_dir
            } else {
                // Fallback to local sidecar dir for development
                std::env::current_dir()
                    .unwrap_or_default()
                    .join("sidecar")
            };

            if working_dir.join("server.py").exists() {
                let resource_dir = app.path().resource_dir().unwrap_or_default();

                // Resolve Python: bundled > venv > system
                let bundled_python = resource_dir.join("resources/python/bin/python3");
                let venv_python = working_dir.join(".venv/bin/python");
                let python = if bundled_python.exists() {
                    bundled_python.to_string_lossy().to_string()
                } else if venv_python.exists() {
                    venv_python.to_string_lossy().to_string()
                } else {
                    "python3".to_string()
                };

                // Resolve Rscript: bundled > system
                let bundled_rscript = resource_dir.join("resources/r-runtime/bin/Rscript");
                let rscript = if bundled_rscript.exists() {
                    bundled_rscript.to_string_lossy().to_string()
                } else {
                    "Rscript".to_string()
                };

                // Set env vars for sidecar to find HPW, CSA, and R
                let skills_root = std::env::var("HEMASUITE_SKILLS_ROOT")
                    .unwrap_or_else(|_| {
                        // Default: parent of the hemasuite project
                        std::env::current_dir()
                            .unwrap_or_default()
                            .parent()
                            .unwrap_or(std::path::Path::new("."))
                            .to_string_lossy()
                            .to_string()
                    });

                match Command::new(&python)
                    .args([
                        "-m",
                        "uvicorn",
                        "server:app",
                        "--host",
                        "127.0.0.1",
                        "--port",
                        "9720",
                    ])
                    .current_dir(&working_dir)
                    .env("RSCRIPT_PATH", &rscript)
                    .env("HPW_PATH", format!("{}/hematology-paper-writer", skills_root))
                    .env("CSA_PATH", format!("{}/clinical-statistics-analyzer", skills_root))
                    .spawn()
                {
                    Ok(child) => {
                        eprintln!("Sidecar started (pid: {})", child.id());
                        app.state::<SidecarState>().0.lock().unwrap().replace(child);
                    }
                    Err(e) => {
                        eprintln!("Failed to start sidecar: {e}");
                    }
                }
            } else {
                eprintln!("Sidecar not found at {:?}, skipping", working_dir);
            }

            Ok(())
        })
        .build(tauri::generate_context!())
        .expect("error while building tauri application")
        .run(|app, event| {
            if let tauri::RunEvent::Exit = event {
                if let Some(mut child) =
                    app.state::<SidecarState>().0.lock().unwrap().take()
                {
                    eprintln!("Stopping sidecar (pid: {})", child.id());
                    let _ = child.kill();
                }
            }
        });
}
