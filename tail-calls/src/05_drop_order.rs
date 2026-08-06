// Section: Watching a frame die
// A value that prints when dropped. With `return`, all the drops happen at the
// end, as the stack unwinds. With `become`, each frame is torn down BEFORE the
// next call. That reordering is the frame being reused, visible from safe Rust.
#![feature(explicit_tail_calls)]

struct Noisy(u64);
impl Drop for Noisy {
    fn drop(&mut self) { println!("  drop Noisy({})", self.0); }
}

fn with_return(n: u64) -> u64 {
    let _local = Noisy(n);
    println!("enter n={}", n);
    if n == 0 { return 0; }
    return with_return(n - 1);
}

fn with_become(n: u64) -> u64 {
    let _local = Noisy(n);
    println!("enter n={}", n);
    if n == 0 { return 0; }
    become with_become(n - 1);
}

fn main() {
    println!("--- return ---"); with_return(2);
    println!("--- become ---"); with_become(2);
}
