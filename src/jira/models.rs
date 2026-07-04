use std::collections::HashMap;

use serde::Deserialize;

use crate::config::schema::CustomFields;

#[derive(Debug, Deserialize)]
pub struct JiraIssue {
    pub key: String,
    pub fields: IssueFields,
}

#[derive(Debug, Deserialize)]
pub struct Issue {
    pub key: String,
    pub parent: ParentIssue,
    pub story_points: Option<f32>,
}

impl Issue {
    pub fn from(issue: JiraIssue, custom_fields: &CustomFields) -> Self {
        let story_points = issue
            .fields
            .custom_fields
            .get(&custom_fields.story_point)
            .and_then(|v| v.as_f64())
            .map(|v| v as f32);

        Self {
            key: issue.key,
            story_points,
            parent: issue.fields.parent,
        }
    }
}

#[derive(Debug, Deserialize)]
pub struct IssueFields {
    pub parent: ParentIssue,

    #[serde(flatten)]
    pub custom_fields: HashMap<String, serde_json::Value>,
}

impl IssueFields {
    pub fn story_points(&self, field_id: &str) -> Option<f32> {
        self.custom_fields
            .get(field_id)
            .and_then(|v| v.as_f64())
            .map(|v| v as f32)
    }
}

#[derive(Debug, Deserialize)]
pub struct ParentIssue {
    pub key: String,
    pub fields: ParentIssueFields,
}

#[derive(Debug, Deserialize)]
pub struct ParentIssueFields {
    pub summary: String,
}

#[derive(Debug, Deserialize)]
pub struct JiraApiResponse<T> {
    pub issues: Option<Vec<T>>,
}
