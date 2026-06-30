use anyhow::{Ok, Result};

use crate::config::load_config;

pub fn handle() -> Result<()> {
    load_config().unwrap();
    //check if config file exist. If no create it
    //
    //ask the user for jira username/password
    //ask the user for harvest username/password

    Ok(())
}
