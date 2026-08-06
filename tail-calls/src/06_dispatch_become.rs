// Section: The case the optimizer cannot fix
// Same program as 06_dispatch.rs, with `become` on both calls.
// Works at every opt-level, including 0.
#![feature(explicit_tail_calls)]
use std::hint::black_box;

type Step = fn(u64) -> u64;

#[inline(never)]
fn even(n: u64) -> u64 {
    if n == 0 { return 0; }
    let next: Step = black_box(odd as Step);
    become next(n - 1)
}

#[inline(never)]
fn odd(n: u64) -> u64 {
    if n == 0 { return 1; }
    let next: Step = black_box(even as Step);
    become next(n - 1)
}

fn main() {
    let n: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);
    println!("=> {}", even(n));
}
