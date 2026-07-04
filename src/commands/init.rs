use std::env;

use anyhow::{Ok, Result};

use crate::{
    config::load_config,
    jira::{JiraClient, JiraConfig},
};

pub async fn handle() -> Result<()> {
    load_config().unwrap();

    env::var("JIRA_EMAIL").expect("Set JIRA_EMAIL env value");
    env::var("JIRA_TOKEN").expect("Set JIRA_TOKEN env value");
    env::var("JIRA_URL").expect("Set JIRA_URL env value");

    env::var("HARVEST_TOKEN").expect("Set HARVEST_TOKEN env value");
    env::var("HARVEST_ACCOUNT_ID").expect("Set HARVEST_ACCOUNT_ID env value");

    let client = JiraClient::new(JiraConfig {
        base_url: env::var("JIRA_URL").unwrap(),
        email: env::var("JIRA_EMAIL").unwrap(),
        api_token: env::var("JIRA_TOKEN").unwrap(),
    });

    let tasks = client.get_tasks_worked_on_current_month().await?;

    println!("{:#?}", tasks);

    Ok(())
}
