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
            Ok(Replicas(raw))
        }

        pub fn count(&self) -> u32 {
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
        Ok(Replicas(raw))
    }

    pub fn count(&self) -> u32 {
        self.0
    }
}

impl TryFrom<u32> for Replicas {
    type Error = &'static str;

    fn try_from(raw: u32) -> Result<Self, Self::Error> {
        Replicas::new(raw)
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
        assert_eq!(smuggled.count(), 0);
    }

    #[test]
    fn try_from_closes_the_hole() {
        let err = serde_json::from_str::<Replicas>("0").unwrap_err();
        assert!(err.to_string().contains("replicas must be at least 1"));

        let ok: Replicas = serde_json::from_str("3").unwrap();
        assert_eq!(ok.count(), 3);
    }
}
