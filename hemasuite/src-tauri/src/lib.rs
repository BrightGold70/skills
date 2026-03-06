use std::process::{Child, Command};
use std::sync::Mutex;
use tauri::menu::{MenuBuilder, MenuItemBuilder, SubmenuBuilder};
use tauri::{Emitter, Manager};

struct SidecarState(Mutex<Option<Child>>);

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

fn resolve_sidecar_dir(app: &tauri::App) -> std::path::PathBuf {
    let sidecar_dir = app
        .path()
        .resource_dir()
        .unwrap_or_default()
        .join("sidecar");

    if sidecar_dir.join("server.py").exists() {
        sidecar_dir
    } else {
        std::env::current_dir()
            .unwrap_or_default()
            .join("sidecar")
    }
}

fn spawn_sidecar(app: &tauri::App, working_dir: &std::path::Path) {
    let resource_dir = app.path().resource_dir().unwrap_or_default();

    let bundled_python = resource_dir.join("resources/python/bin/python3");
    let venv_python = working_dir.join(".venv/bin/python");
    let python = if bundled_python.exists() {
        bundled_python.to_string_lossy().to_string()
    } else if venv_python.exists() {
        venv_python.to_string_lossy().to_string()
    } else {
        "python3".to_string()
    };

    let bundled_rscript = resource_dir.join("resources/r-runtime/bin/Rscript");
    let rscript = if bundled_rscript.exists() {
        bundled_rscript.to_string_lossy().to_string()
    } else {
        "Rscript".to_string()
    };

    let skills_root = std::env::var("HEMASUITE_SKILLS_ROOT").unwrap_or_else(|_| {
        std::env::current_dir()
            .unwrap_or_default()
            .parent()
            .unwrap_or(std::path::Path::new("."))
            .to_string_lossy()
            .to_string()
    });

    match Command::new(&python)
        .args([
            "-m", "uvicorn", "server:app",
            "--host", "127.0.0.1", "--port", "9720",
        ])
        .current_dir(working_dir)
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
}

fn show_splash_window(app: &tauri::App) {
    // Write splash HTML to a temp file for the webview to load
    let splash_html = include_str!("../../src/splash.html");
    let splash_path = std::env::temp_dir().join("hemasuite-splash.html");
    let _ = std::fs::write(&splash_path, splash_html);

    let splash_url = tauri::WebviewUrl::External(
        format!("file://{}", splash_path.display())
            .parse()
            .expect("valid splash URL"),
    );

    let _splash = tauri::WebviewWindowBuilder::new(app, "splash", splash_url)
        .title("HemaSuite")
        .inner_size(480.0, 320.0)
        .resizable(false)
        .decorations(false)
        .center()
        .always_on_top(true)
        .build();
}

fn poll_health_then_show_main(app: &tauri::App) {
    let app_handle = app.handle().clone();
    std::thread::spawn(move || {
        // Poll: try connecting every 500ms for up to 30s
        let max_attempts = 60;
        for _ in 0..max_attempts {
            std::thread::sleep(std::time::Duration::from_millis(500));
            if let Ok(mut stream) = std::net::TcpStream::connect("127.0.0.1:9720") {
                use std::io::Write;
                let _ = stream.write_all(b"GET /health HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n");
                let _ = stream.flush();
                // Sidecar is up — show main window, close splash
                if let Some(main_win) = app_handle.get_webview_window("main") {
                    let _ = main_win.show();
                }
                if let Some(splash_win) = app_handle.get_webview_window("splash") {
                    let _ = splash_win.close();
                }
                return;
            }
        }
        // Timeout — show main window anyway
        eprintln!("Sidecar health check timed out, showing main window");
        if let Some(main_win) = app_handle.get_webview_window("main") {
            let _ = main_win.show();
        }
        if let Some(splash_win) = app_handle.get_webview_window("splash") {
            let _ = splash_win.close();
        }
    });
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(SidecarState(Mutex::new(None)))
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![greet])
        .setup(|app| {
            let working_dir = resolve_sidecar_dir(app);

            if working_dir.join("server.py").exists() {
                show_splash_window(app);
                spawn_sidecar(app, &working_dir);
                poll_health_then_show_main(app);
            } else {
                eprintln!("Sidecar not found at {:?}, skipping", working_dir);
                // No sidecar — show main window immediately
                if let Some(main_win) = app.get_webview_window("main") {
                    let _ = main_win.show();
                }
            }

            // macOS native menu with keyboard shortcuts
            let file_menu = SubmenuBuilder::new(app, "File")
                .item(
                    &MenuItemBuilder::with_id("new-project", "New Project")
                        .accelerator("CmdOrCtrl+N")
                        .build(app)?,
                )
                .item(
                    &MenuItemBuilder::with_id("open-project", "Open Project")
                        .accelerator("CmdOrCtrl+O")
                        .build(app)?,
                )
                .item(
                    &MenuItemBuilder::with_id("save", "Save")
                        .accelerator("CmdOrCtrl+S")
                        .build(app)?,
                )
                .separator()
                .close_window()
                .build()?;

            let edit_menu = SubmenuBuilder::new(app, "Edit")
                .undo()
                .redo()
                .separator()
                .cut()
                .copy()
                .paste()
                .select_all()
                .build()?;

            let view_menu = SubmenuBuilder::new(app, "View")
                .item(
                    &MenuItemBuilder::with_id("tab-hpw", "HPW Editor")
                        .accelerator("CmdOrCtrl+1")
                        .build(app)?,
                )
                .item(
                    &MenuItemBuilder::with_id("tab-csa", "CSA Dashboard")
                        .accelerator("CmdOrCtrl+2")
                        .build(app)?,
                )
                .item(
                    &MenuItemBuilder::with_id("tab-pipeline", "Pipeline")
                        .accelerator("CmdOrCtrl+3")
                        .build(app)?,
                )
                .build()?;

            let menu = MenuBuilder::new(app)
                .items(&[&file_menu, &edit_menu, &view_menu])
                .build()?;

            app.set_menu(menu)?;

            app.on_menu_event(move |app_handle, event| {
                let id = event.id().0.as_str();
                let _ = app_handle.emit("menu-event", id);
            });

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
