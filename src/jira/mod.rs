mod client;

pub use client::JiraClient;

pub struct JiraConfig {
    pub base_url: String,
    pub email: String,
    pub api_token: String,
}

