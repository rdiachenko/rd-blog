# Rate limiting

Java implementations of four rate limiting algorithms, the companion code for the [Rate Limiting](https://rdiachenko.com/series/rate-limiting/) series. Each limiter is one class with one method, `allowed(userId)`, which returns whether the request may go through. Every constructor takes a `Clock`, so the tests move time by hand instead of sleeping.

| Post | Class | Constructor arguments |
|---|---|---|
| [Fixed window](https://rdiachenko.com/posts/arch/rate-limiting/fixed-window-algorithm/) | [`FixedWindowRateLimiter`](src/main/java/com/rdiachenko/ratelimiting/FixedWindowRateLimiter.java) | `maxCount, windowDuration, clock` |
| [Sliding window](https://rdiachenko.com/posts/arch/rate-limiting/sliding-window-algorithm/) | [`SlidingWindowLogRateLimiter`](src/main/java/com/rdiachenko/ratelimiting/SlidingWindowLogRateLimiter.java), keeps every timestamp | `maxCount, windowDuration, clock` |
| | [`SlidingWindowCountRateLimiter`](src/main/java/com/rdiachenko/ratelimiting/SlidingWindowCountRateLimiter.java), keeps two counters | `maxCount, windowDuration, clock` |
| [Token bucket](https://rdiachenko.com/posts/arch/rate-limiting/token-bucket-algorithm/) | [`TokenBucketRateLimiter`](src/main/java/com/rdiachenko/ratelimiting/TokenBucketRateLimiter.java) | `capacity, period, tokensPerPeriod, clock, refillStrategy` |
| [Leaky bucket](https://rdiachenko.com/posts/arch/rate-limiting/leaky-bucket-algorithm/) | [`LeakyBucketRateLimiter`](src/main/java/com/rdiachenko/ratelimiting/LeakyBucketRateLimiter.java) | `capacity, period, leaksPerPeriod, clock` |

The limiters keep per-user state in a plain `HashMap` and are not thread safe. They exist to show how each algorithm works, not to be dropped into a server. The posts explain the algorithms and carry the flow diagrams.

Run the tests:

```bash
./gradlew test
```

Needs Java 21. Gradle downloads a matching JDK through the toolchain resolver if none is installed.
