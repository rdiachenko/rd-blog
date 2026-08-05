//! Checks interleaved with effects, versus parse-then-act.
//! Post section: "Shotgun parsing".

use crate::domain::Deploy;
use crate::request::DeployRequest;
use crate::validate_first::{is_environment, is_service_name, DeployError};

#[derive(Debug, Default)]
pub struct World {
    pub deployments: Vec<String>,
    pub traffic: Vec<String>,
    pub audit: Vec<String>,
}

/// Each check is correct in isolation. The problem is the ordering: two writes
/// land before the third check runs.
pub fn deploy_shotgun(
    world: &mut World,
    req: &DeployRequest,
) -> Result<(), DeployError> {
    if !is_service_name(&req.service) {
        return Err(DeployError::BadServiceName);
    }
    // effect 1
    world.deployments.push(req.service.clone());

    if !is_environment(&req.environment) {
        return Err(DeployError::UnknownEnvironment);
    }
    // effect 2
    let route = format!("{} -> {}", req.environment, req.service);
    world.traffic.push(route);

    if req.replicas == 0 {
        // too late
        return Err(DeployError::ZeroReplicas);
    }

    let entry = format!("deployed {} to {}", req.service, req.environment);
    world.audit.push(entry);
    Ok(())
}

/// Takes a `Deploy`, not a `DeployRequest`. Raw input cannot reach it.
pub fn deploy(world: &mut World, deploy: &Deploy) {
    world.deployments.push(deploy.service.as_str().to_owned());
    world.traffic.push(format!(
        "{} -> {}",
        deploy.environment.name(),
        deploy.service.as_str()
    ));
    world.audit.push(format!(
        "deployed {} to {}",
        deploy.service.as_str(),
        deploy.environment.name()
    ));
}

#[cfg(test)]
mod tests {
    use super::*;

    fn zero_replica_request() -> DeployRequest {
        DeployRequest {
            service: "checkout-api".into(),
            environment: "production".into(),
            replicas: 0,
        }
    }

    #[test]
    fn shotgun_leaves_partial_state_behind_after_rejecting() {
        let mut world = World::default();
        let err = deploy_shotgun(&mut world, &zero_replica_request());

        assert_eq!(err, Err(DeployError::ZeroReplicas));
        // Rejected, and yet:
        assert_eq!(world.deployments, ["checkout-api"]);
        assert_eq!(world.traffic, ["production -> checkout-api"]);
        // ...while the record that would explain it was never written.
        assert!(world.audit.is_empty());
    }

    #[test]
    fn parse_first_changes_nothing_when_the_input_is_rejected() {
        let mut world = World::default();

        // The effects never get a Deploy, because there is no Deploy to get.
        let parsed = Deploy::try_from(zero_replica_request());
        assert_eq!(parsed, Err(crate::domain::ParseError::ZeroReplicas));
        if let Ok(parsed) = parsed {
            deploy(&mut world, &parsed);
        }

        assert!(world.deployments.is_empty());
        assert!(world.traffic.is_empty());
        assert!(world.audit.is_empty());
    }
}
