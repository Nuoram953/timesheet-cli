use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct Issue {
    pub key: String,
    pub fields: IssueFields,
}

#[derive(Debug, Deserialize)]
pub struct IssueFields {
    pub parent: ParentIssue,
}

#[derive(Debug, Deserialize)]
pub struct ParentIssue {
    pub key: String,
}

#[derive(Debug, Deserialize)]
pub struct JiraApiResponse<T> {
    pub issues: Option<Vec<T>>,
}
