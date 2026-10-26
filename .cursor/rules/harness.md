# Rule: agent harness
- Follow the loop in docs/harness_engineering.md: observe → route (Jev) → plan → tools → verify → respond.
- Add new behaviour as a graph node with typed state fields; respect max 6 steps and 3 tool calls.
- New tools need typed input/output schemas, seller scoping and an error shape.
- Never let an LLM output set a payment verdict or release goods.
- Mid confidence (0.60–0.90) always goes to the seller (human in the loop).
- Every node writes a trace entry.
