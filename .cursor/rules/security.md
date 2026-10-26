# Rule: security
- Never commit .env, keys or tokens; new variables go in .env.example (names only).
- Verify webhook signatures on the raw body; dedupe by event id.
- No real phone numbers, account numbers or receipts in the repo, tests or logs.
- Test-mode payment keys only during the hackathon.
