use crate::jira::{
    models::{Issue, JiraApiResponse},
    JiraConfig,
};

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

    fn build_auth_header(self) -> String {
        use base64::prelude::*;
        let credentials = format!("{}:{}", self.email, self.api_token);
        format!("Basic {}", BASE64_STANDARD.encode(credentials.as_bytes()))
    }

    fn search_issues(&self, jql: &str) -> Result<Vec<Issue>, JiraError> {
        let url = format!("{}/rest/api/3/search", self.base_url);

        let response = self
            .http
            .get(&url)
            .header("Authorization", self.build_auth_header())
            .header("Accept", "application/json")
            .query(&[("jql", jql)])
            .send()?;

        if response.status() == reqwest::StatusCode::UNAUTHORIZED {
            return Err(JiraError::Unauthorized);
        }

        let body: JiraApiResponse = response.json()?;
        Ok(body.issues.unwrap())
    }

    pub fn get_tasks_worked_on_current_month(&self) -> Result<Vec<Issue>, JiraError> {
        let jql =
            "status CHANGED BY currentUser() DURING (startOfMonth(), endOfMonth())".to_string();
        self.search_issues(&jql)
    }
}

#[derive(thiserror::Error, Debug)]
pub enum JiraError {
    #[error("Jira auth failed — check email/token")]
    Unauthorized,
}
