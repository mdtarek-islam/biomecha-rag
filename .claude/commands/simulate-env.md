---
description: Run the local Lambda and API Gateway harness with service fakes, then report cold-start and load latency.
argument-hint: "[requests] [concurrency]"
---

Use the env-simulation-tester agent. Arguments: $ARGUMENTS (default: 200 requests, concurrency 10).

1. Build events for valid, malformed, oversize and base64 bodies.
2. Run them through the handler with the Pinecone and Hugging Face fakes. Open no network socket.
3. Inject faults: timeout, 429, 503 and malformed JSON. Check each status code.
4. Measure cold start in a fresh interpreter. Report import time.
5. Run the load probe. Report p50, p95 and p99 latency and the error rate.

Print one summary table. Save the raw numbers under tests/harness/results/ (not tracked).
