// Section: The stack is a finite thing
// Every call reserves a frame. Frames are never reclaimed until the call returns.
// Run it twice: 100_000 succeeds, 200_000 dies.

fn sum(n: u64, acc: u64) -> u64 {
    if n == 0 { return acc; }
    sum(n - 1, acc + n)
}

fn main() {
    let n: u64 = std::env::args().nth(1).and_then(|s| s.parse().ok()).unwrap_or(100_000);
    println!("sum(1..={}) = {}", n, sum(n, 0));
}
