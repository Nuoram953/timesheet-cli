use anyhow::{Context, Result};
use directories::ProjectDirs;
use serde::Deserialize;
use std::{fs, io, path::PathBuf};

use crate::config::schema::{GeneralSettings, RecurringEntry};

const APP_NAME: &str = "timesheet";
const CONFIG_FILE: &str = "config.toml";

pub mod schema;

#[derive(Debug, Deserialize)]
pub struct Config {
    pub general: GeneralSettings,
    pub recurring: Vec<RecurringEntry>,
}

pub fn config_dir() -> io::Result<PathBuf> {
    let project_dirs = ProjectDirs::from("", "", APP_NAME).ok_or_else(|| {
        io::Error::new(
            io::ErrorKind::NotFound,
            "Unable to determine config directory",
        )
    })?;

    Ok(project_dirs.config_dir().to_path_buf())
}

pub fn ensure_rules_file() -> io::Result<PathBuf> {
    let dir = config_dir()?;
    fs::create_dir_all(&dir)?;

    let path = dir.join(CONFIG_FILE);

    if !path.exists() {
        fs::write(&path, DEFAULT_CONFIG)?;
    }

    Ok(path)
}

pub fn load_config() -> Result<Config> {
    let path = ensure_rules_file().context("failed to ensure config file exists")?;

    let contents = fs::read_to_string(&path).context("failed to read config file")?;

    let config: Config = toml::from_str(&contents).context("failed to parse TOML config")?;

    println!("{:?}", config);

    Ok(config)
}

const DEFAULT_CONFIG: &str = r#"
[[recurring]]
name = "Daily standup"
cron = "0 9 * * MON-FRI"
duration_minutes = 15
"#;
