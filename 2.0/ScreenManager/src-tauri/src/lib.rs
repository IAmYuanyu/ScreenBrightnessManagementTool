use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use tauri::State;
use std::sync::Mutex;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Monitor {
    pub id: u32,
    pub name: String,
    pub width: u32,
    pub height: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Settings {
    pub brightness_presets: Vec<u32>,
    pub method: String,
    pub hotkey_up: String,
    pub hotkey_down: String,
}

pub struct AppState {
    pub current_brightness: Mutex<HashMap<u32, u32>>,
    pub settings: Mutex<Settings>,
}

#[tauri::command]
fn get_monitors() -> Vec<Monitor> {
    vec![
        Monitor {
            id: 0,
            name: "Display 1".to_string(),
            width: 1920,
            height: 1080,
        },
        Monitor {
            id: 1,
            name: "Display 2".to_string(),
            width: 1920,
            height: 1080,
        },
    ]
}

#[tauri::command]
fn set_brightness(monitor_id: u32, brightness: u32, state: State<AppState>) -> Result<(), String> {
    let mut brightness_map = state.current_brightness.lock().unwrap();
    brightness_map.insert(monitor_id, brightness);

    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("powershell")
            .args(&[
                "-NoProfile",
                "-Command",
                &format!(
                    "$monitors = Get-WmiObject -Namespace root\\wmi -Class WmiMonitorBrightnessMethods; if ($monitors) {{ $monitors | ForEach-Object {{ $_.WmiSetBrightness(1, {}) }} }}",
                    brightness
                ),
            ])
            .output();
    }

    Ok(())
}

#[tauri::command]
fn turn_off_display() -> Result<(), String> {
    #[cfg(target_os = "windows")]
    {
        let _ = Command::new("powershell")
            .args(&[
                "-NoProfile",
                "-Command",
                "Get-WmiObject -Namespace root\\wmi -Class WmiMonitorBrightnessMethods | ForEach-Object { $_.WmiSetBrightness(1, 0) }",
            ])
            .output();
    }
    Ok(())
}

#[tauri::command]
fn create_mask(monitor_id: u32, color: String, alpha: u32) -> Result<(), String> {
    Ok(())
}

#[tauri::command]
fn close_mask(monitor_id: u32) -> Result<(), String> {
    Ok(())
}

#[tauri::command]
fn save_settings(settings: Settings, state: State<AppState>) -> Result<(), String> {
    let mut app_settings = state.settings.lock().unwrap();
    *app_settings = settings.clone();

    let config_dir = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
    let config_path = config_dir.join("screen_manager_settings.json");
    let json = serde_json::to_string(&settings).map_err(|e| e.to_string())?;
    fs::write(config_path, json).map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
fn load_settings(_state: State<AppState>) -> Result<Settings, String> {
    let config_dir = dirs::config_dir().unwrap_or_else(|| PathBuf::from("."));
    let config_path = config_dir.join("screen_manager_settings.json");

    if config_path.exists() {
        let json = fs::read_to_string(config_path).map_err(|e| e.to_string())?;
        let settings: Settings = serde_json::from_str(&json).map_err(|e| e.to_string())?;
        Ok(settings)
    } else {
        Ok(Settings {
            brightness_presets: vec![30, 50, 75, 100],
            method: "brightness".to_string(),
            hotkey_up: "Ctrl+Alt+Up".to_string(),
            hotkey_down: "Ctrl+Alt+Down".to_string(),
        })
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let app_state = AppState {
        current_brightness: Mutex::new(HashMap::new()),
        settings: Mutex::new(Settings {
            brightness_presets: vec![30, 50, 75, 100],
            method: "brightness".to_string(),
            hotkey_up: "Ctrl+Alt+Up".to_string(),
            hotkey_down: "Ctrl+Alt+Down".to_string(),
        }),
    };

    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        .manage(app_state)
        .invoke_handler(tauri::generate_handler![
            get_monitors,
            set_brightness,
            turn_off_display,
            create_mask,
            close_mask,
            save_settings,
            load_settings,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
