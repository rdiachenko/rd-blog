# Predictions

Each prediction was written before measuring, and the prediction lines haven't
changed since. The "Measured" and "Gap and why" lines were added after each measurement.

## 1. Weight memory

- Parameters: 5174964736
- Bytes per parameter: 2 (BF16)
- Prediction: 9.64 GiB
- Measured: 8.56 GiB on the GPU ("Model loading took 8.56 GiB memory"). The model files on disk
  come to 9.64 GiB, matching the prediction.
- Gap and why: 1.08 GiB less loaded than stored. The model files store the token lookup table
  twice (`embed_tokens` and `lm_head.weight`, 635,699,200 parameters, 1.18 GiB each). The config
  ties them (`tie_word_embeddings: true`), so vLLM loads one copy for both. Expected
  9.64 − 1.18 = 8.46 GiB, measured 8.56 GiB. The remaining 0.10 GiB is unexplained.

```text
(EngineCore pid=26718) INFO 11-06 22:32:40 [model_runner.py:428] Model loading took 8.56 GiB memory and 3.764822 seconds
...
(EngineCore pid=26718) INFO 11-06 22:33:54 [gpu_worker.py:1066] Free memory on device (14.71/15.51 GiB) on startup. Desired GPU memory utilization is (0.85, 13.18 GiB). Actual usage is 8.71 GiB for consumed memory (weights + non-torch), 1.69 GiB for peak activation, and 0.06 GiB for CUDAGraph memory. Replace gpu_memory_utilization config with `--kv-cache-memory=2762986804` (2.57 GiB) to fit into requested memory, or `--kv-cache-memory=4411499008` (4.11 GiB) to fully utilize gpu memory. Current kv cache memory in use is 2.78 GiB.
```

## 2. Tokens per screenshot

- Image: 1280 × 800 after resizing
- Each token covers 32 × 32 pixels (patch 16, merge 2 × 2)
- Prediction: 1000 tokens per screenshot
- Prompt at step 1: about 1000 + 50 = 1050 (one screenshot plus system prompt, task and question)
- Prompt at step 10: about 10 × 1000 + 300 = 10300 (10 screenshots plus all the text)
- Measured: exactly 1000 image tokens per screenshot (`multimodal_tokens` in the response). The
  1280 × 803 screenshots are rounded to 1280 × 800. Prompt at step 1 of the agent run: 1,063 to
  1,067 tokens. At step 10: 10,348 to 10,352.
- Gap and why: none worth the name. The text guesses were close: each step adds about 30 tokens
  of text (the action and the question) on top of the 1000 for its screenshot.

## 3. Fastest possible decode speed, 1 agent

- Weights read per token: 10.35 GB
- Memory bandwidth: 896 GB/s (source: https://www.nvidia.com/en-gb/geforce/graphics-cards/50-series/rtx-5070-family/)
- Prediction: at least 11.6 ms per token, so at most 86 tokens per second
- Each step generates 64 tokens, so decoding takes at least 64 × 11.6 ms = 742.4 ms per step
- Measured: 11.3 ms per token, faster than the 11.6 ms "floor". It's the same in every run at
  step 1, and grows to 11.7 ms by step 10.
- Gap and why: the floor counted bytes the GPU doesn't read per token.
  - The second copy of the lookup table is never loaded. The real size on the GPU is 8.56 GiB
    ("Model loading took 8.56 GiB"), which is 9.19 GB (8.56 × 1024³ ÷ 1000³).
  - The vision encoder only runs while reading screenshots. Generating text uses only the
    language part. The 4 vision groups (`model.visual.*` in `list_tensors.py`) hold 333,514,240
    parameters, 0.67 GB.
  - Bytes actually read per token: 9.19 − 0.67 = 8.52 GB.
  - Corrected floor: 8.52 ÷ 896 = 9.51 ms per token.
  - Achieved bandwidth: 8.52 ÷ 0.0113 = 754 GB/s, 84% of 896 (memory bandwidth utilisation).
  - Left out: the request's own KV cache and linear-attention state, which the GPU also reads per
    token. At step 1 that's about 85 MB (33 MB of attention KV for about 1,000 tokens, plus 50 MB
    of linear-attention state), about 1% of the total. Including it raises MBU by about a point.
  - If the unexplained 0.10 GiB from prediction 1 isn't weights, the bytes read are a little lower
    and MBU comes out about 83%.
  - The growth to 11.7 ms at step 10 matches the KV cache: 10,350 tokens × 32,768 bytes per token
    = 339 MB more read per token, 0.38 ms at 896 GB/s. Measured increase: 0.36 ms.

## 4. KV cache capacity

- Not predicted: I didn't yet know how to compute KV bytes per token for this hybrid model.
- Measured: 78,444 tokens ("GPU KV cache size" in the log), from 2.78 GiB of KV cache memory.
- Prediction for the 8-agent run: at step 10, 8 agents need about 8 × 10,300 = 82400 tokens.
  That doesn't fit in 78,444, so I expect the server fail with out of memory.
- Measured: the server didn't fail. vLLM queued the requests it couldn't fit (log: "Running: 7
  reqs, Waiting: 1 reqs") and kept going. 8 agents: from step 7, TTFT 2.5 to 5 s, decode 60 to
  137 ms per token, total output 90 tokens per second against 166 with 4 agents. 6 agents: fine
  until step 9, collapse at step 10.
- Gap and why:
  - No failure: vLLM kept the requests that didn't fit waiting until there was room, instead of
    failing.
  - Earlier than predicted: the slowdown started at about 58,000 to 62,000 tokens of total
    history, not 78,444. In the 6-agent run, vLLM's counters show 46,080 fewer cache hits than expected,
    the equivalent of 80 blocks of 576 tokens, and no preemptions. That points to cached history
    being evicted between steps.
  - Still open: why the useful limit is 74 to 79% of the reported capacity. My guess is that the
    linear-attention layers, which share the GPU memory pool with the KV cache, need more of it
    than the 78,444 figure allows for, but I haven't checked it.

```text
(EngineCore pid=26718) INFO 11-06 22:33:50 [kv_cache_utils.py:1147] GPU KV cache size: 78,444 tokens, Maximum concurrency for 32,768 tokens per request: 2.39x

(APIServer pid=35291) INFO 11-07 12:58:57 [loggers.py:335] Engine 000: Avg prompt throughput: 5796.3 tokens/s, Avg generation throughput: 43.8 tokens/s, Running: 7 reqs, Waiting: 1 reqs, GPU KV cache usage: 89.8%, Prefix cache hit rate: 54.3%, MM cache hit rate: 81.5%
```
