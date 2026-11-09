import base64
import time
from pathlib import Path

from openai import OpenAI

client = OpenAI(base_url="http://localhost:8000/v1", api_key="unused")
image = base64.b64encode(Path("shots/01.png").read_bytes()).decode()

start = time.perf_counter()
stream = client.chat.completions.create(
    model="Hcompany/Holo-3.1-4B",
    messages=[{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image}"}},
            {"type": "text", "text": "Task: find the British Library's opening hours. What is the next action?"},
        ],
    }],
    max_tokens=64,
    temperature=0,
    stream=True,
    stream_options={"include_usage": True},
    extra_body={"ignore_eos": True},
)

first_token_at = None
usage = None
text = []
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        if first_token_at is None:
            first_token_at = time.perf_counter()
        text.append(chunk.choices[0].delta.content)
    if chunk.usage:
        usage = chunk.usage
end = time.perf_counter()

ttft = first_token_at - start
decode = (end - first_token_at) / (usage.completion_tokens - 1)
print("".join(text))
print(usage)
print(f"TTFT {ttft * 1000:.0f} ms, decode {decode * 1000:.1f} ms per token, total {(end - start) * 1000:.0f} ms")

