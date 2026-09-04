#!/usr/bin/env bash
# Reproduces every result in the post. Needs stable rustc and a nightly toolchain:
#   rustup toolchain install nightly
set -u
cd "$(dirname "$0")"
SRC=src
OUT=$(mktemp -d)
trap 'rm -rf "$OUT"' EXIT

run() {  # run <binary> <args...> -> "ok <output>" or "OVERFLOW"
  local out code
  out=$("$@" 2>&1); code=$?
  if [ $code -ne 0 ]; then echo "OVERFLOW"; else echo "$out"; fi
}

echo "=== 1. The stack is finite (opt-level=0) ==="
rustc --edition 2024 -C opt-level=0 $SRC/01_overflow.rs -o "$OUT/01" 2>/dev/null
printf '  depth   100000  %s\n' "$(run "$OUT/01" 100000)"
printf '  depth   200000  %s\n' "$(run "$OUT/01" 200000)"

echo
echo "=== 2. Frames march down the stack ==="
rustc --edition 2024 -C opt-level=0 $SRC/02_frames.rs -o "$OUT/02" 2>/dev/null
"$OUT/02" | head -4
echo "  ..."

echo
echo "=== 3. Tail vs non-tail across opt levels (depth 10,000,000) ==="
printf '  %-10s %-12s %s\n' "opt-level" "tail" "not_tail"
for opt in 0 1 2 3; do
  rustc --edition 2024 -C opt-level=$opt $SRC/03_opt_levels.rs -o "$OUT/03_$opt" 2>/dev/null
  t=$(run "$OUT/03_$opt" tail 10000000);  t=${t%% n=*}; [ "$t" != OVERFLOW ] && t=ok
  u=$(run "$OUT/03_$opt" nottail 10000000); u=${u%% n=*}; [ "$u" != OVERFLOW ] && u=ok
  printf '  %-10s %-12s %s\n' "$opt" "$t" "$u"
done

echo
echo "=== 4. become at opt-level=0, depth 10,000,000 ==="
rustup run nightly rustc --edition 2024 -C opt-level=0 $SRC/04_become.rs -o "$OUT/04" 2>/dev/null
printf '  %s\n' "$(run "$OUT/04" 10000000)"

echo
echo "=== 5. Drop order: return vs become ==="
rustup run nightly rustc --edition 2024 -C opt-level=0 $SRC/05_drop_order.rs -o "$OUT/05" 2>/dev/null
"$OUT/05" | sed 's/^/  /'

echo
echo "=== 6. Opaque dispatch: no opt-level saves it (depth 1,000,000) ==="
printf '  %-10s %-12s %s\n' "opt-level" "plain call" "become"
for opt in 0 1 2 3; do
  rustc --edition 2024 -C opt-level=$opt $SRC/06_dispatch.rs -o "$OUT/06_$opt" 2>/dev/null
  rustup run nightly rustc --edition 2024 -C opt-level=$opt $SRC/06_dispatch_become.rs -o "$OUT/06b_$opt" 2>/dev/null
  p=$(run "$OUT/06_$opt" 1000000);  [ "$p" != OVERFLOW ] && p=ok
  b=$(run "$OUT/06b_$opt" 1000000); [ "$b" != OVERFLOW ] && b=ok
  printf '  %-10s %-12s %s\n' "$opt" "$p" "$b"
done

echo
echo "=== 7. The instructions ==="
rustup run nightly rustc --edition 2024 -C opt-level=0 --emit asm $SRC/07_asm.rs -o "$OUT/07.s" 2>/dev/null
echo "  plain (recursive call):"
awk '/^_plain:/,/ret/' "$OUT/07.s" | grep -E '^\s+(bl|b)\s+_plain' | sed 's/^/    /'
echo "  tailcall (become):"
awk '/^_tailcall:/{f=1} f&&/\.cfi_endproc/{exit} f' "$OUT/07.s" \
  | grep -E '^\s+(ldp\s+x29|add\s+sp|b\s+_tailcall)' | tail -3 | sed 's/^/    /'
