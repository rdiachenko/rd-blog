//! The validating version: the checks run, and their result is thrown away.
//! Post section: "The same code in Rust".

use crate::domain::ENVIRONMENTS;
use crate::request::DeployRequest;

#[derive(Debug, PartialEq, Eq)]
pub enum DeployError {
    BadServiceName,
    UnknownEnvironment,
    ZeroReplicas,
}

impl std::fmt::Display for DeployError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::BadServiceName => write!(f, "service must be 3-30 chars of [a-z0-9-]"),
            Self::UnknownEnvironment => write!(f, "environment is not one of the known ones"),
            Self::ZeroReplicas => write!(f, "replicas must be at least 1"),
        }
    }
}

impl std::error::Error for DeployError {}

// NOTE: the post calls these two helpers without showing them.
//
// They check the RAW string, exactly like the Java `@Pattern` annotations do,
// so they are deliberately not equivalent to `ServiceName::parse` and
// `Environment::parse`, which canonicalise first:
//
//     is_service_name("CHECKOUT-API")     == false
//     ServiceName::parse("CHECKOUT-API")  == Ok(ServiceName("checkout-api"))
//
// That gap is the post's point about normalising after checking. It is also the
// cost of having the same rule written twice.
pub fn is_service_name(raw: &str) -> bool {
    let len_ok = (3..=30).contains(&raw.len());
    let chars_ok = raw
        .chars()
        .all(|c| c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-');
    len_ok && chars_ok
}

pub fn is_environment(raw: &str) -> bool {
    ENVIRONMENTS.contains(&raw)
}

pub fn validate(req: &DeployRequest) -> Result<(), DeployError> {
    if !is_service_name(&req.service) {
        return Err(DeployError::BadServiceName);
    }
    if !is_environment(&req.environment) {
        return Err(DeployError::UnknownEnvironment);
    }

    if req.replicas == 0 {
        return Err(DeployError::ZeroReplicas);
    }

    Ok(())
}

/// Nothing in this signature says `validate` ran first.
pub fn memory_per_replica_mb(req: &DeployRequest, total_mb: u32) -> u32 {
    total_mb / req.replicas
}

#[cfg(test)]
mod tests {
    use super::*;

    fn req(service: &str, environment: &str, replicas: u32) -> DeployRequest {
        DeployRequest {
            service: service.to_string(),
            environment: environment.to_string(),
            replicas,
        }
    }

    /// The two paths are not interchangeable. `validate` checks the raw string,
    /// `ServiceName::parse` canonicalises first, so they disagree on input that
    /// only differs by case or padding.
    #[test]
    fn validate_and_parse_disagree_on_uncanonical_input() {
        use crate::domain::Deploy;

        let r = req("CHECKOUT-API", "production", 3);
        assert_eq!(validate(&r), Err(DeployError::BadServiceName));
        assert!(Deploy::try_from(r).is_ok());
    }

    #[test]
    fn validate_accepts_a_good_request() {
        assert_eq!(validate(&req("checkout-api", "production", 3)), Ok(()));
    }

    /// The point of the post: this compiles, type-checks, and panics.
    #[test]
    #[should_panic(expected = "attempt to divide by zero")]
    fn nothing_stops_you_from_skipping_the_check() {
        let r = req("checkout-api", "production", 0);
        let _ = memory_per_replica_mb(&r, 1024);
    }
}
