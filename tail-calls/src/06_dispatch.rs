// Section: The case the optimizer cannot fix
// Each step decides at run time which function runs next, so the optimizer
// cannot see through the call and cannot flatten it. This overflows at EVERY
// opt-level. `black_box` stands in for a real dispatch table; an interpreter
// with 256 opcodes gets this opacity for free.
use std::hint::black_box;

type Step = fn(u64) -> u64;

#[inline(never)]
fn even(n: u64) -> u64 {
    if n == 0 { return 0; }
    let next: Step = black_box(odd as Step);
    next(n - 1)
}

#[inline(never)]
fn odd(n: u64) -> u64 {
    if n == 0 { return 1; }
    let next: Step = black_box(even as Step);
    next(n - 1)
}

fn main() {
    let n: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(1_000_000);
    println!("=> {}", even(n));
}
