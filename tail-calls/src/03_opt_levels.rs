// Section: Does the compiler already fix this?
// Two shapes: one tail-recursive, one NOT. Build at each -C opt-level
// and see which survives. The result is not the one most articles predict.

#[inline(never)]
fn tail(n: u64, acc: u64) -> u64 {
    if n == 0 { return acc; }
    tail(n - 1, acc + n)          // tail position: nothing happens after the call
}

#[inline(never)]
fn not_tail(n: u64) -> u64 {
    if n == 0 { return 0; }
    n + not_tail(n - 1)           // NOT tail position: the add happens after
}

fn main() {
    let which = std::env::args().nth(1).unwrap_or_default();
    let n: u64 = std::env::args().nth(2).and_then(|s| s.parse().ok()).unwrap_or(10_000_000);
    let r = if which == "tail" { tail(n, 0) } else { not_tail(n) };
    println!("{} n={} => {}", which, n, r);
}
