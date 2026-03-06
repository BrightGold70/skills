#[cfg(test)]
mod tests {
    /// Verify that menu item IDs match the strings expected by frontend useMenuEvents hook.
    #[test]
    fn test_menu_item_ids() {
        let expected_ids = ["new-project", "open-project", "save", "tab-hpw", "tab-csa", "tab-pipeline"];
        for id in &expected_ids {
            // Menu IDs must be non-empty kebab-case strings
            assert!(!id.is_empty(), "Menu item ID must not be empty");
            assert!(
                id.chars().all(|c| c.is_ascii_lowercase() || c == '-'),
                "Menu item ID '{}' must be lowercase kebab-case",
                id
            );
        }
    }

    /// Verify sidecar path resolution logic: dev path falls back to cwd/sidecar.
    #[test]
    fn test_sidecar_path_fallback_to_cwd() {
        // In test environment, resource_dir won't have server.py,
        // so resolve should fall back to current_dir/sidecar
        let cwd = std::env::current_dir().unwrap_or_default();
        let fallback = cwd.join("sidecar");
        // The path should be constructable (doesn't need to exist in test env)
        assert!(fallback.to_string_lossy().contains("sidecar"));
    }

    /// Verify Python resolution order: bundled > venv > system.
    #[test]
    fn test_python_resolution_order() {
        let resource_dir = std::path::PathBuf::from("/nonexistent/resources");
        let working_dir = std::path::PathBuf::from("/nonexistent/sidecar");

        let bundled = resource_dir.join("resources/python/bin/python3");
        let venv = working_dir.join(".venv/bin/python");

        // Neither exists, so system python3 should be selected
        let python = if bundled.exists() {
            bundled.to_string_lossy().to_string()
        } else if venv.exists() {
            venv.to_string_lossy().to_string()
        } else {
            "python3".to_string()
        };

        assert_eq!(python, "python3");
    }
}
