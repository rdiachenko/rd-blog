//! The serde boundary, from the post's "Parsing at the boundary" section.
//!
//!     cargo run --example boundary
//!
//! Kept out of `main.rs` so that `cargo run` prints exactly the shotgun-parsing
//! comparison the post shows.

use parse_dont_validate::domain::Deploy;

fn main() {
    let json = r#"{"service":"checkout-api","environment":"production","replicas":0}"#;
    let err = serde_json::from_str::<Deploy>(json).unwrap_err();
    println!("rejected at the boundary -> {err}");

    let json = r#"{"service":"  CHECKOUT-API  ","environment":"Production","replicas":4}"#;
    let parsed = serde_json::from_str::<Deploy>(json).unwrap();
    println!(
        "parsed and canonicalised -> {}/{} x{}",
        parsed.environment.name(),
        parsed.service.as_str(),
        parsed.replicas.get()
    );
}
