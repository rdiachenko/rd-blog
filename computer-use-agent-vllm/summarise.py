import csv
import sys
from collections import defaultdict
from statistics import mean

by_step = defaultdict(list)
for row in csv.DictReader(open(sys.argv[1])):
    by_step[(row["label"], int(row["step"]))].append(row)


def avg(rows, key):
    return mean(float(r[key]) for r in rows)


print("| Step | Prompt tokens | Cached (on) | TTFT off | TTFT on | Step off | Step on |")
print("|---|---|---|---|---|---|---|")
total = {"off": 0.0, "on": 0.0}
for step in range(1, 11):
    off, on = by_step[("off", step)], by_step[("on", step)]
    total["off"] += avg(off, "step_ms")
    total["on"] += avg(on, "step_ms")
    print(
        f"| {step} | {avg(on, 'prompt_tokens'):,.0f} | {avg(on, 'cached_tokens'):,.0f} "
        f"| {avg(off, 'ttft_ms'):,.0f} ms | {avg(on, 'ttft_ms'):,.0f} ms "
        f"| {avg(off, 'step_ms'):,.0f} ms | {avg(on, 'step_ms'):,.0f} ms |"
    )
print(f"| **All 10** | | | | | **{total['off'] / 1000:.2f} s** | **{total['on'] / 1000:.2f} s** |")

for label in ("off", "on"):
    ttfts = [float(r["ttft_ms"]) for r in by_step[(label, 10)]]
    print(f"\n{label}: {len(ttfts)} runs, step 10 TTFT spread {max(ttfts) - min(ttfts):.1f} ms")

