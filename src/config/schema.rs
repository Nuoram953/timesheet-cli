use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct GeneralSettings {
    pub issue_tracker: String,
    pub time_tracker: String,
}

#[derive(Debug, Deserialize)]
pub struct RecurringEntry {
    pub name: String,
    pub cron: String,
    pub duration_minutes: usize,
}
