use crate::jira::JiraConfig;

pub struct JiraClient {
    http: reqwest::Client,
    base_url: String,
    email: String,
    api_token: String,
}

impl JiraClient {
    pub fn new(config: JiraConfig) -> Self {
        JiraClient {
            http: reqwest::Client::new(),
            base_url: config.base_url,
            email: config.email,
            api_token: config.api_token,
        }
    }
}
