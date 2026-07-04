use chrono::{DateTime, Utc};
use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Issue {
    pub key: String,
}

#[derive(Debug, Deserialize)]
pub struct JiraApiResponse<T> {
    pub issues: Option<Vec<T>>,
    pub total: Option<u32>,
    #[serde(rename = "startAt")]
    pub start_at: Option<u32>,
    #[serde(rename = "maxResults")]
    pub max_results: Option<u32>,
}
