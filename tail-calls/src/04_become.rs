// Section: Asking for the guarantee
// Identical to 03's `tail`, plus one keyword. Build with opt-level=0:
// the optimizer is switched off, and 10 million frames still work.
#![feature(explicit_tail_calls)]

#[inline(never)]
fn sum(n: u64, acc: u64) -> u64 {
    if n == 0 { return acc; }
    become sum(n - 1, acc + n)
}

fn main() {
    let n: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(10_000_000);
    println!("sum(1..={}) = {}", n, sum(n, 0));
}
