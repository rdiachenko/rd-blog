//! The parsed domain types. Post section: "Refining the type".
//!
//! Every primitive field is private, so the only way to get a `ServiceName`,
//! `Environment` or `Replicas` from outside this module is through its fallible
//! constructor. `Deploy`'s own fields are public because their types are
//! already parsed, so there is nothing left to protect.

use std::fmt;
use std::num::NonZeroU32;

use serde::Deserialize;

use crate::request::DeployRequest;

#[derive(Debug, PartialEq, Eq)]
pub enum ParseError {
    BadServiceName,
    UnknownEnvironment,
    ZeroReplicas,
}

impl std::error::Error for ParseError {}

// serde reports a `try_from` failure as a string, so ParseError needs Display.
// Post section: "Parsing at the boundary".
impl fmt::Display for ParseError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::BadServiceName => {
                write!(f, "service must be 3-30 chars of [a-z0-9-]")
            }
            Self::UnknownEnvironment => {
                write!(
                    f,
                    "environment must be one of {}",
                    ENVIRONMENTS.join(", ")
                )
            }
            Self::ZeroReplicas => {
                write!(f, "replicas must be at least 1")
            }
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct ServiceName(String);

impl ServiceName {
    pub fn parse(raw: &str) -> Result<Self, ParseError> {
        let canonical = raw.trim().to_ascii_lowercase();

        let len_ok = (3..=30).contains(&canonical.len());
        let chars_ok = canonical.chars().all(|c| {
            c.is_ascii_lowercase() || c.is_ascii_digit() || c == '-'
        });

        if len_ok && chars_ok {
            Ok(Self(canonical))
        } else {
            Err(ParseError::BadServiceName)
        }
    }

    pub fn as_str(&self) -> &str {
        &self.0
    }
}

pub const ENVIRONMENTS: [&str; 3] = ["dev", "staging", "production"];

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Environment(&'static str);

impl Environment {
    pub fn parse(raw: &str) -> Result<Self, ParseError> {
        let canonical = raw.trim().to_ascii_lowercase();

        ENVIRONMENTS
            .into_iter()
            .find(|name| *name == canonical)
            .map(Environment)
            .ok_or(ParseError::UnknownEnvironment)
    }

    pub fn name(self) -> &'static str {
        self.0
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Replicas(NonZeroU32);

impl Replicas {
    pub fn new(raw: u32) -> Result<Self, ParseError> {
        let count = NonZeroU32::new(raw).ok_or(ParseError::ZeroReplicas)?;
        Ok(Self(count))
    }

    /// Hands back the `NonZeroU32`, not a plain `u32`. Dividing by this has no
    /// zero case for the compiler to check.
    pub fn get(self) -> NonZeroU32 {
        self.0
    }
}

// Deliberately no `#[derive(Default)]`: the empty string is not a service name
// and zero is not a replica count.

/// The composite. serde builds a `DeployRequest` first, then routes it through
/// the `TryFrom` impl below, so nothing downstream of `from_str` ever sees the
/// raw shape.
#[derive(Debug, Clone, PartialEq, Eq, Hash, Deserialize)]
#[serde(try_from = "DeployRequest")]
pub struct Deploy {
    pub service: ServiceName,
    pub environment: Environment,
    pub replicas: Replicas,
}

impl TryFrom<DeployRequest> for Deploy {
    type Error = ParseError;

    fn try_from(req: DeployRequest) -> Result<Self, Self::Error> {
        Ok(Self {
            service: ServiceName::parse(&req.service)?,
            environment: Environment::parse(&req.environment)?,
            replicas: Replicas::new(req.replicas)?,
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parse_canonicalises_before_checking() {
        let name = ServiceName::parse("  CHECKOUT-API  ").unwrap();
        assert_eq!(name.as_str(), "checkout-api");
    }

    /// The post's `std` snippet: dividing by a `NonZeroU32` directly, rather
    /// than calling `.get()` first, leaves no zero case for the compiler.
    #[test]
    fn dividing_by_nonzero_needs_no_zero_case() {
        let total: u32 = 1024;
        let workers = NonZeroU32::new(4).unwrap();
        let per_worker = total / workers;
        assert_eq!(per_worker, 256);
    }

    #[test]
    fn zero_replicas_has_no_representation() {
        assert_eq!(Replicas::new(0), Err(ParseError::ZeroReplicas));
        assert_eq!(Replicas::new(3).unwrap().get().get(), 3);
    }

    #[test]
    fn unknown_environment_is_rejected() {
        assert_eq!(
            Environment::parse("qa"),
            Err(ParseError::UnknownEnvironment)
        );
        assert_eq!(
            Environment::parse("Production").unwrap().name(),
            "production"
        );
    }

    #[test]
    fn serde_routes_through_try_from() {
        let json = r#"{
    "service": "checkout-api",
    "environment": "production",
    "replicas": 0
}"#;
        let err = serde_json::from_str::<Deploy>(json).unwrap_err();
        assert!(err.to_string().contains("replicas must be at least 1"));
    }

    #[test]
    fn canonicalisation_happens_once_at_the_boundary() {
        let a = r#"{
    "service": "CHECKOUT-API",
    "environment": "production",
    "replicas": 2
}"#;
        let b = r#"{
    "service": "  checkout-api ",
    "environment": "Production",
    "replicas": 2
}"#;
        assert_eq!(
            serde_json::from_str::<Deploy>(a).unwrap(),
            serde_json::from_str::<Deploy>(b).unwrap()
        );
    }

    // Post section: "Outside the `domain` module, constructing an invalid
    // ServiceName is a compile error rather than a review comment."
    //
    //     let sneaky = ServiceName("Not A Service".to_string());
    //     // error[E0603]: tuple struct constructor `ServiceName` is private
}
