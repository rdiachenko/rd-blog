//! The runnable comparison from the post's "Shotgun parsing" section.
//!
//! `main` prints [`run`] verbatim, and the post reproduces that text in a
//! `console` block. The test at the bottom pins the exact output, so changing
//! the formatting here fails `cargo test` instead of silently making the
//! published post wrong.

use crate::domain::Deploy;
use crate::request::DeployRequest;
use crate::shotgun::{World, deploy, deploy_shotgun};

fn zero_replica_request() -> DeployRequest {
    DeployRequest {
        service: "checkout-api".into(),
        environment: "production".into(),
        replicas: 0,
    }
}

fn section(label: &str, outcome: &str, world: &World) -> String {
    format!(
        "{label:<11} -> {outcome}\n  \
         deployments : {:?}\n  \
         traffic     : {:?}\n  \
         audit       : {:?}",
        world.deployments, world.traffic, world.audit
    )
}

/// Runs both deploy paths against the same rejected request and renders the
/// comparison the post shows.
#[must_use]
pub fn run() -> String {
    // Checks interleaved with effects: rejected, but state already changed.
    let mut world = World::default();
    let req = zero_replica_request();
    let outcome = match deploy_shotgun(&mut world, &req) {
        Ok(()) => "accepted".to_owned(),
        Err(e) => format!("rejected with {e:?}"),
    };
    let shotgun = section("shotgun", &outcome, &world);

    // Parse first: the effects take a Deploy, so they never run.
    let mut world = World::default();
    let outcome = match Deploy::try_from(zero_replica_request()) {
        Ok(parsed) => {
            deploy(&mut world, &parsed);
            "accepted".to_owned()
        }
        Err(e) => format!("rejected with {e:?}"),
    };
    let parse_first = section("parse-first", &outcome, &world);

    format!("{shotgun}\n\n{parse_first}")
}

#[cfg(test)]
mod tests {
    use super::run;

    /// This exact text appears in the post as a `console` block under
    /// "Shotgun parsing". If you change the formatting in `section`, update the
    /// post to match, or delete the block from it.
    const EXPECTED: &str = "\
shotgun     -> rejected with ZeroReplicas
  deployments : [\"checkout-api\"]
  traffic     : [\"production -> checkout-api\"]
  audit       : []

parse-first -> rejected with ZeroReplicas
  deployments : []
  traffic     : []
  audit       : []";

    #[test]
    fn demo_output_matches_the_post() {
        assert_eq!(run(), EXPECTED);
    }
}
