use crate::{config::load_config, jira::{
    JiraConfig, models::{Issue, JiraApiResponse, JiraIssue}
}};

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

    fn build_auth_header(&self) -> String {
        use base64::prelude::*;
        let credentials = format!("{}:{}", self.email, self.api_token);
        format!("Basic {}", BASE64_STANDARD.encode(credentials.as_bytes()))
    }

    async fn search_issues(&self, jql: &str) -> Result<Vec<Issue>, JiraError> {
        let config = load_config().unwrap();
        let url = format!("{}/rest/api/3/search/jql", self.base_url);

        let response = self
            .http
            .get(&url)
            .header("Authorization", self.build_auth_header())
            .header("Accept", "application/json")
            .query(&[("jql", jql), ("fields", "*all"), ("maxResults", "5000")])
            .send()
            .await?;

        if response.status() == reqwest::StatusCode::UNAUTHORIZED {
            return Err(JiraError::Unauthorized);
        }

        let body = response.text().await?;

        let json: serde_json::Value = serde_json::from_str(&body)?;
        println!("{}", serde_json::to_string_pretty(&json)?);

        let api_response: JiraApiResponse<JiraIssue> = serde_json::from_str(&body)?;

        let issues: Vec<Issue> = api_response
            .issues
            .unwrap_or_default()
            .into_iter()
            .map(|jira_issue: JiraIssue| Issue::from(jira_issue, &config.custom_fields))
            .collect();

        Ok(issues)
    }

    pub async fn get_tasks_worked_on_current_month(&self) -> Result<Vec<Issue>, JiraError> {
        let jql =
            "status CHANGED BY currentUser() DURING (startOfMonth(), endOfMonth())".to_string();
        self.search_issues(&jql).await
    }
}

#[derive(thiserror::Error, Debug)]
pub enum JiraError {
    #[error("Jira auth failed — check email/token")]
    Unauthorized,
    #[error("HTTP error: {0}")]
    Http(#[from] reqwest::Error),
    #[error("HTTP error: {0}")]
    Parsing(#[from] serde_json::Error),
}
