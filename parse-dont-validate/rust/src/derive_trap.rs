//! `#[derive(Deserialize)]` on a newtype reaches past the private field.
//! Post section: "The derive that skips your constructor".

use serde::Deserialize;

/// The trap. This is the common spelling, and it is the wrong one.
pub mod trap {
    use serde::Deserialize;

    #[derive(Debug, Deserialize, PartialEq)]
    pub struct Replicas(u32); // private field

    impl Replicas {
        pub fn new(raw: u32) -> Result<Self, &'static str> {
            if raw == 0 {
                return Err("replicas must be at least 1");
            }
            Ok(Self(raw))
        }

        pub fn get(&self) -> u32 {
            self.0
        }
    }
}

/// The fix: route deserialisation through `TryFrom`.
#[derive(Debug, Deserialize, PartialEq)]
#[serde(try_from = "u32")]
pub struct Replicas(u32);

impl Replicas {
    pub fn new(raw: u32) -> Result<Self, &'static str> {
        if raw == 0 {
            return Err("replicas must be at least 1");
        }
        Ok(Self(raw))
    }

    pub fn get(&self) -> u32 {
        self.0
    }
}

impl TryFrom<u32> for Replicas {
    type Error = &'static str;

    fn try_from(raw: u32) -> Result<Self, Self::Error> {
        Self::new(raw)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn derive_bypasses_constructor() {
        assert!(trap::Replicas::new(0).is_err());

        // ...and yet deserialisation accepts zero.
        let smuggled: trap::Replicas = serde_json::from_str("0").unwrap();
        assert_eq!(smuggled.get(), 0);
    }

    /// The hole exists only because the inner type is `u32`. Pushing the rule
    /// into the inner type closes it without any serde attribute at all.
    #[test]
    fn a_nonzero_inner_type_has_no_hole() {
        use std::num::NonZeroU32;

        #[derive(Debug, Deserialize)]
        struct Replicas(NonZeroU32);

        let err = serde_json::from_str::<Replicas>("0").unwrap_err();
        assert!(err.to_string().contains("nonzero"));

        let ok: Replicas = serde_json::from_str("3").unwrap();
        assert_eq!(ok.0.get(), 3);
    }

    #[test]
    fn try_from_closes_the_hole() {
        let err = serde_json::from_str::<Replicas>("0").unwrap_err();
        assert!(err.to_string().contains("replicas must be at least 1"));

        let ok: Replicas = serde_json::from_str("3").unwrap();
        assert_eq!(ok.get(), 3);
    }
}
