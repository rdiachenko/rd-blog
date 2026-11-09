import base64
import csv
import io
import sys
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean

from openai import OpenAI
from PIL import Image

MODEL = "Hcompany/Holo-3.1-4B"
TASK = "Find the British Library's opening hours for the building, the Reading Rooms and the Treasures Gallery."
QUESTION = "What is the next action?"
ACTIONS = [
    '{"action": "click", "target": "The British Library search result"}',
    '{"action": "click", "target": "Visit"}',
    '{"action": "click", "target": "menu"}',
    '{"action": "click", "target": "Opening hours"}',
    '{"action": "click", "target": "Library building opening hours"}',
    '{"action": "scroll", "direction": "down"}',
    '{"action": "scroll", "direction": "down"}',
    '{"action": "click", "target": "Reading Rooms opening hours"}',
    '{"action": "click", "target": "Treasures Gallery opening hours"}',
]

client = OpenAI(base_url="http://localhost:8000/v1", api_key="unused")


def image_part(b64):
    return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}


def load_shots(run_id):
    """1 pixel changed per run, so vLLM's image cache can't reuse an earlier run's screenshots."""
    seed = int(run_id, 16)
    color = (seed % 256, (seed >> 8) % 256, (seed >> 16) % 256)
    shots = []
    for path in sorted(Path("shots").glob("*.png")):
        img = Image.open(path).convert("RGB")
        img.putpixel((0, 0), color)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        shots.append(base64.b64encode(buf.getvalue()).decode())
    return shots


def build_messages(run_id, shots, step):
    messages = [{"role": "system", "content": f"Run {run_id}. You are a computer-use agent operating a web browser."}]
    for i in range(step + 1):
        content = [{"type": "text", "text": f"Task: {TASK}"}] if i == 0 else []
        content += [image_part(shots[i]), {"type": "text", "text": QUESTION}]
        messages.append({"role": "user", "content": content})
        if i < step:
            messages.append({"role": "assistant", "content": ACTIONS[i]})
    return messages


def measure(messages):
    start = time.perf_counter()
    stream = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=64,
        temperature=0,
        stream=True,
        stream_options={"include_usage": True},
        extra_body={"ignore_eos": True},
    )
    first_token_at, usage = None, None
    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content and first_token_at is None:
            first_token_at = time.perf_counter()
        if chunk.usage:
            usage = chunk.usage
    end = time.perf_counter()
    return {
        "prompt_tokens": usage.prompt_tokens,
        "cached_tokens": usage.prompt_tokens_details.cached_tokens,
        "ttft_ms": round((first_token_at - start) * 1000, 1),
        "decode_ms_per_token": round((end - first_token_at) * 1000 / (usage.completion_tokens - 1), 2),
        "step_ms": round((end - start) * 1000, 1),
    }


def warm_up():
    buf = io.BytesIO()
    Image.new("RGB", (1280, 803), "white").save(buf, format="PNG")
    blank = base64.b64encode(buf.getvalue()).decode()
    measure([{"role": "user", "content": [image_part(blank), {"type": "text", "text": QUESTION}]}])


def run_agent(run_id, shots):
    return [{"step": step + 1, **measure(build_messages(run_id, shots, step))} for step in range(len(shots))]


label = sys.argv[1]
agents = int(sys.argv[2])
warm_up()

run_ids = [uuid.uuid4().hex[:8] for _ in range(agents)]
shots_per_agent = [load_shots(run_id) for run_id in run_ids]

start = time.perf_counter()
with ThreadPoolExecutor(max_workers=agents) as pool:
    results = list(pool.map(run_agent, run_ids, shots_per_agent))
wall_s = time.perf_counter() - start

rows = [
    {"label": label, "agents": agents, "agent": a, **row}
    for a, agent_rows in enumerate(results)
    for row in agent_rows
]

print(f"{agents} agents, {wall_s:.1f} s wall time, {agents * 10 * 64 / wall_s:.0f} generated tokens per second")
for step in range(1, 11):
    step_rows = [r for r in rows if r["step"] == step]
    print(
        f"step {step:2}: TTFT mean {mean(r['ttft_ms'] for r in step_rows):5.0f} ms, "
        f"max {max(r['ttft_ms'] for r in step_rows):5.0f} ms, "
        f"decode {mean(r['decode_ms_per_token'] for r in step_rows):5.2f} ms per token, "
        f"step {mean(r['step_ms'] for r in step_rows):5.0f} ms"
    )

out = Path(f"results-{agents}-agents.csv")
new_file = not out.exists()
with out.open("a", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0]))
    if new_file:
        writer.writeheader()
    writer.writerows(rows)

