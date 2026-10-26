# Database migrations

Apply in order:

1. `0001_init.sql` - core schema (sellers, products, buyers, orders, payments, evidence, verdicts, fraud_signals, messages, webhook_events, daily_summaries).
2. `0002_catalog_drafts.sql` - pending product drafts from seller photos.
3. `0003_traces.sql` - trace table and speech metadata on messages.

Run in the Supabase SQL editor or via `supabase db push`. The API uses the service role key; RLS is enabled but no anon policies exist yet.
