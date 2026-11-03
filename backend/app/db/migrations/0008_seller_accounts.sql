-- Seller login accounts (Supabase Auth) linked to connected Instagram shops.
-- Lets a logged-in seller restore their saved Instagram session after a
-- browser/server restart without reconnecting Instagram. Apply in the
-- Supabase SQL editor. The API uses the service role key.

create table if not exists seller_accounts (
    user_id uuid primary key,
    email text not null default '',
    ig_account_id text not null,
    username text not null default '',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists seller_accounts_ig_account_id_idx
    on seller_accounts (ig_account_id);

alter table seller_accounts enable row level security;

comment on table seller_accounts is
    'Supabase Auth user -> Instagram shop link for dashboard login/restore. No tokens here; tokens live in instagram_sessions.';
