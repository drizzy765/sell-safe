-- Instagram OAuth sessions (survive API restarts / Render spin-down).
-- Tokens stay server-side; the browser only holds an opaque session id.
-- Apply in the Supabase SQL editor. The API uses the service role key.

create table if not exists instagram_sessions (
    session_id text primary key,
    access_token text not null,
    account_id text not null,
    username text not null default '',
    alias_ids jsonb not null default '[]'::jsonb,
    created_at timestamptz not null default now(),
    expires_at timestamptz
);

create index if not exists instagram_sessions_account_id_idx
    on instagram_sessions (account_id);

alter table instagram_sessions enable row level security;

comment on table instagram_sessions is
    'Instagram Login sessions for connected shops. access_token is a secret: service role only, never expose to clients.';
