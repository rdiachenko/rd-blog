//! The parsing version. Same function, one word different in the signature,
//! and the divide-by-zero case is gone. Post section: "Refining the type".

use crate::domain::Deploy;

pub fn memory_per_replica_mb(deploy: &Deploy, total_mb: u32) -> u32 {
    total_mb / deploy.replicas.get()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::request::DeployRequest;

    #[test]
    fn a_deploy_cannot_carry_zero_replicas() {
        let req = DeployRequest {
            service: "checkout-api".into(),
            environment: "production".into(),
            replicas: 0,
        };
        // There is no way to reach memory_per_replica_mb with a zero divisor:
        // the only route to a Deploy is through try_from, and it rejects this.
        assert!(Deploy::try_from(req).is_err());
    }

    #[test]
    fn divides_without_a_panic_path() {
        let req = DeployRequest {
            service: "checkout-api".into(),
            environment: "production".into(),
            replicas: 4,
        };
        let deploy = Deploy::try_from(req).unwrap();
        assert_eq!(memory_per_replica_mb(&deploy, 1024), 256);
    }
}
