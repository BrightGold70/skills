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
                // Try venv python first, then system python3
                let venv_python = working_dir.join(".venv/bin/python");
                let python = if venv_python.exists() {
                    venv_python.to_string_lossy().to_string()
                } else {
                    "python3".to_string()
                };

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
