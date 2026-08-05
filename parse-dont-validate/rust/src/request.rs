//! The raw request as it arrives on the wire. It mirrors the JSON and nothing
//! more. Post sections: "The same code in Rust", "Parsing at the boundary".

use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct DeployRequest {
    pub service: String,
    pub environment: String,
    pub replicas: u32,
}
