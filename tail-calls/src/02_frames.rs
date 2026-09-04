// Section: Seeing the frames
// Print the address of a local at each depth. The addresses march downward,
// one frame apart. That gap IS the frame size.

#[inline(never)]
fn sum(n: u64, acc: u64) -> u64 {
    let marker = n;
    let addr = &marker as *const u64 as usize;
    if n % 1000 == 0 || n < 3 {
        println!("n = {:>6}   local at {:#x}", n, addr);
    }
    if n == 0 { return acc; }
    sum(n - 1, acc + n)
}

fn main() { println!("=> {}", sum(5000, 0)); }
