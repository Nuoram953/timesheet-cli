use chrono::{DateTime, Utc};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Issue {
    pub key: String,
    pub summary: String,
    pub description: Option<serde_json::Value>,
    pub status: String,
    pub priority: Option<String>,
    pub assignee: Option<String>,
    pub reporter: Option<String>,
    pub created: DateTime<Utc>,
    pub updated: DateTime<Utc>,
    pub issue_type: String,
}

#[derive(Debug, Deserialize)]
pub struct JiraApiResponse {
    pub issues: Option<Vec<Issue>>,
    pub total: Option<u32>,
    #[serde(rename = "startAt")]
    pub start_at: Option<u32>,
    #[serde(rename = "maxResults")]
    pub max_results: Option<u32>,
}
