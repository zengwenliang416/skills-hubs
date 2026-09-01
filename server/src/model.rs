use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize)]
pub struct MetricsResponse {
    pub total_visitors: u64,
    pub today_visitors: u64,
    pub total_page_views: u64,
    pub daily_visitors: Vec<DailyVisitors>,
    pub npm_downloads: Vec<NpmDownload>,
    pub skill_engagement: Vec<SkillEngagement>,
}

#[derive(Debug, Serialize)]
pub struct DailyVisitors {
    pub date: String,
    pub visitors: u64,
}

#[derive(Clone, Debug, Serialize)]
pub struct NpmDownload {
    pub package_name: String,
    pub downloads: Option<u64>,
    pub period_start: Option<String>,
    pub period_end: Option<String>,
    pub stale: bool,
    pub error: Option<String>,
}

#[derive(Clone, Copy, Debug, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum SkillEventType {
    SkillView,
    InstallCopy,
    DocumentationClick,
    RepositoryClick,
}

impl SkillEventType {
    pub fn as_str(self) -> &'static str {
        match self {
            Self::SkillView => "skill_view",
            Self::InstallCopy => "install_copy",
            Self::DocumentationClick => "documentation_click",
            Self::RepositoryClick => "repository_click",
        }
    }
}

#[derive(Debug, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct SkillEventRequest {
    pub skill_name: String,
    pub event_type: SkillEventType,
}

#[derive(Clone, Debug, Serialize)]
pub struct SkillEngagement {
    pub skill_name: String,
    pub unique_visitors: u64,
    pub views: u64,
    pub install_copies: u64,
    pub documentation_clicks: u64,
    pub repository_clicks: u64,
}

#[derive(Debug, Serialize)]
pub struct ErrorResponse {
    pub error: String,
}

#[derive(Debug, Serialize)]
pub struct HealthResponse {
    pub status: &'static str,
    pub retention: RetentionHealthResponse,
}

#[derive(Clone, Debug, Serialize)]
pub struct RetentionHealthResponse {
    pub healthy: bool,
    pub last_success_at: Option<String>,
    pub last_failure_at: Option<String>,
}

#[cfg(test)]
mod tests {
    use super::SkillEventRequest;

    #[test]
    fn parses_fixed_skill_event() {
        let event: SkillEventRequest = serde_json::from_str(
            r#"{"skill_name":"image-api-workbench","event_type":"install_copy"}"#,
        )
        .expect("valid event");

        assert_eq!(event.skill_name, "image-api-workbench");
        assert_eq!(event.event_type.as_str(), "install_copy");
    }

    #[test]
    fn rejects_unknown_event_and_fields() {
        assert!(
            serde_json::from_str::<SkillEventRequest>(
                r#"{"skill_name":"one","event_type":"search"}"#
            )
            .is_err()
        );
        assert!(
            serde_json::from_str::<SkillEventRequest>(
                r#"{"skill_name":"one","event_type":"skill_view","metadata":"extra"}"#
            )
            .is_err()
        );
    }
}
