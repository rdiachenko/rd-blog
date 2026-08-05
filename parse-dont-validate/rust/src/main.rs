//! `cargo run` reproduces the shotgun-parsing output from the post.
//! `cargo test` runs every claim the post makes as an assertion.
//! `cargo run --example boundary` shows the serde boundary.

fn main() {
    println!("{}", parse_dont_validate::demo::run());
}
