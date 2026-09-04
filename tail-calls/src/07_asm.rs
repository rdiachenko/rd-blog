// Section: Three instructions
// Build with:  rustc -C opt-level=0 --emit asm 07_asm.rs
// Then read _plain and _tailcall in 07_asm.s.
#![feature(explicit_tail_calls)]

#[unsafe(no_mangle)]
#[inline(never)]
pub fn plain(n: u64, acc: u64) -> u64 {
    if n == 0 { return acc; }
    plain(n - 1, acc + n)
}

#[unsafe(no_mangle)]
#[inline(never)]
pub fn tailcall(n: u64, acc: u64) -> u64 {
    if n == 0 { return acc; }
    become tailcall(n - 1, acc + n)
}

fn main() { println!("{} {}", plain(3, 0), tailcall(3, 0)); }
