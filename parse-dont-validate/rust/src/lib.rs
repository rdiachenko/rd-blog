#![allow(clippy::must_use_candidate, clippy::missing_errors_doc)]
// The snippets in this crate mirror the post. Sprinkling `#[must_use]` and
// `# Errors` sections through them would make the published code diverge from
// what a reader sees, so those two pedantic lints are allowed on purpose.

//! Runnable companion to "Parse, Don't Validate, in Rust".
//! <https://rdiachenko.com/posts/rust/parse-dont-validate/>
//!
//! Each module maps to a section of the post:
//!
//! | Module            | Post section                          |
//! |-------------------|---------------------------------------|
//! | `request`         | The same code in Rust                 |
//! | `validate_first`  | The same code in Rust                 |
//! | `domain`          | Refining the type                     |
//! | `parse_first`     | Refining the type                     |
//! | `illegal_states`  | Removing invalid states               |
//! | `shotgun`         | Shotgun parsing                       |
//! | `derive_trap`     | The derive that skips your constructor|

pub mod demo;
pub mod derive_trap;
pub mod domain;
pub mod illegal_states;
pub mod parse_first;
pub mod request;
pub mod shotgun;
pub mod validate_first;
