use std::env;

use anyhow::{Ok, Result};

use crate::config::load_config;

pub fn handle() -> Result<()> {
    load_config().unwrap();

    env::var("JIRA_EMAIL").expect("Set JIRA_EMAIL env value");
    env::var("JIRA_TOKEN").expect("Set JIRA_TOKEN env value");

    env::var("HARVEST_TOKEN").expect("Set HARVEST_TOKEN env value");
    env::var("HARVEST_ACCOUNT_ID").expect("Set HARVEST_ACCOUNT_ID env value");

    Ok(())
}
