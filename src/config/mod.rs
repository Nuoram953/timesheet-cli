use anyhow::{Context, Result};
use directories::ProjectDirs;
use serde::Deserialize;
use std::{fs, io, path::PathBuf};

const APP_NAME: &str = "timesheet";
const CONFIG_FILE: &str = "config.toml";

#[derive(Debug, Deserialize)]
pub struct Config {}

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
        fs::write(&path, DEFAULT_RULES)?;
    }

    Ok(path)
}

pub fn load_config() -> Result<Config> {
    let path = ensure_rules_file().context("failed to ensure config file exists")?;

    let contents = fs::read_to_string(&path).context("failed to read config file")?;

    let config: Config = toml::from_str(&contents).context("failed to parse TOML config")?;

    Ok(config)
}

const DEFAULT_RULES: &str = r#"
default_branch: main
rules:
  - name: deploy_change_requires_traffic
    type: file
    match:
      - deploy
      - scripts/deploy
    warning: "Deploy script changed → did you update traffic script?"
"#;
