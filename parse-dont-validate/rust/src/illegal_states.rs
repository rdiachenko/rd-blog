//! Restructuring: stop invalid combinations from being representable at all.
//! Post section: "Removing invalid states".

/// 4 fields, 16 combinations, only a few of which describe a real deployment.
/// `is_running && is_finished` compiles. So does finished with no timestamp.
pub struct DeploymentRow {
    pub is_running: bool,
    pub is_finished: bool,
    pub finished_at_ms: Option<u64>,
    pub failure_reason: Option<String>,
}

/// 4 states, 4 variants, each carrying exactly the data that state needs.
/// Adding a fifth variant makes every incomplete match fail to compile.
pub enum Deployment {
    Queued,
    RollingOut { started_at_ms: u64 },
    Live { since_ms: u64 },
    RolledBack { reason: String },
}

impl Deployment {
    pub fn describe(&self) -> String {
        match self {
            Deployment::Queued => "queued".to_string(),
            Deployment::RollingOut { started_at_ms } => {
                format!("rolling out since {started_at_ms}")
            }
            Deployment::Live { since_ms } => {
                format!("live since {since_ms}")
            }
            Deployment::RolledBack { reason } => {
                format!("rolled back: {reason}")
            }
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn the_row_shape_allows_states_that_cannot_exist() {
        // Both running and finished, and finished without a timestamp.
        // The type system has no objection.
        let nonsense = DeploymentRow {
            is_running: true,
            is_finished: true,
            finished_at_ms: None,
            failure_reason: None,
        };
        assert!(nonsense.is_running && nonsense.is_finished);
        assert!(nonsense.finished_at_ms.is_none());
        assert!(nonsense.failure_reason.is_none());
    }

    #[test]
    fn the_enum_shape_has_no_impossible_arm() {
        assert_eq!(Deployment::Queued.describe(), "queued");
        assert_eq!(
            Deployment::Live { since_ms: 42 }.describe(),
            "live since 42"
        );
    }
}
