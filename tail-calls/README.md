# Tail calls

Companion code for "Recursion in Rust Is a Bet on the Optimiser". Every
experiment in the post is one file here, and `run.sh` reproduces every table and
code block in order.

```bash
rustup toolchain install nightly   # `become` is nightly-only
./run.sh
```

The whole run takes under a minute. Most of it is building the same 15-line
program at four optimisation levels.

| File | Post section | Shows |
|---|---|---|
| `src/01_overflow.rs` | The stack is a finite thing | 100k frames fit, 200k don't |
| `src/02_frames.rs` | Seeing the frames | Frame addresses marching downward |
| `src/03_opt_levels.rs` | Does the compiler already fix this? | Tail and non-tail both survive at `opt-level=1` |
| `src/04_become.rs` | Asking for the guarantee | 10M frames with the optimiser off |
| `src/05_drop_order.rs` | Watching a frame die | `become` drops locals before the call |
| `src/06_dispatch.rs` | The case the optimiser can't fix | Overflows at every `opt-level` |
| `src/06_dispatch_become.rs` | The case the optimiser can't fix | Same program, `become`, works everywhere |
| `src/07_asm.rs` | Three instructions | `bl` versus teardown plus `b` |

## Requirements

`become` is behind `#![feature(explicit_tail_calls)]` and needs nightly. The
feature is incomplete, so nightly prints a warning on every build; `run.sh`
silences it.

`07_asm.rs` prints aarch64 assembly, because that's what an Apple Silicon Mac
emits. On x86-64 the same two functions come out as `call` versus `jmp`, with the
frame teardown ahead of the `jmp`. The shape of the argument is identical; the
mnemonics aren't.

## Why `black_box` in the dispatch example

`06_dispatch.rs` picks the next function through `std::hint::black_box`, which
tells the optimiser to assume nothing about the value. Without it, LLVM reads the
function pointer, sees exactly which function runs next, and flattens the
recursion; that version survives at `opt-level=1`.

`black_box` is standing in for something real. An interpreter dispatching 256
opcodes through a table gets the same opacity for free, which is why interpreters
are the usual reason people want guaranteed tail calls.

## The one number worth checking yourself

`07_asm.rs` compiles `plain` to a frame of 64 bytes (`sub sp, sp, #64`). The main
thread gets 8 MB of stack by default, so the arithmetic predicts a crash at
roughly 131,072 frames:

```text
8 * 1024 * 1024 / 64 = 131072
```

Bisecting `01_overflow.rs` puts the real limit between 129,841 and 131,793. The
prediction lands inside the measured window, which is a good sign the model of
the stack in the post is the right one.
