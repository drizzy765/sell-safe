# P0 live-proof package

- Generated: 2026-10-30T21:44:21.173833+00:00
- Mode: automated TestClient (Paystack verify mocked; no real Naira moved)

## Results

- Paystack path -> CONFIRMED + release: PASS (webhook=200, release=200, status=released)
- Edited screenshot -> SUSPICIOUS / release 409: PASS (release=409, status=awaiting_payment)

## Manual follow-up (real Paystack test mode)

1. Create an order against a Paystack test DVA.
2. Complete a test transfer; confirm webhook signature uses `PAYSTACK_SECRET_KEY`.
3. Expect CONFIRMED and release allowed.
4. Send an edited-amount screenshot; expect SUSPICIOUS and release 409.
5. Drop screen recordings into `demo/clips/` as `confirmed.mp4` and `suspicious.mp4`.
