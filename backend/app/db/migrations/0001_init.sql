-- Sell-Safe initial schema. See docs/data_model.md.
-- Money is integer kobo (bigint). Timestamps are UTC timestamptz.
-- Apply once on the Supabase project (SQL editor or supabase db push).

create extension if not exists vector with schema extensions;

create type seller_language as enum ('en', 'pcm', 'yo');
create type order_status as enum (
    'draft',
    'awaiting_payment',
    'payment_review',
    'paid',
    'released',
    'delivered',
    'cancelled'
);
create type payment_method as enum ('bank_transfer', 'virtual_account', 'crypto');
create type payment_status as enum ('pending', 'confirmed', 'not_found', 'suspicious');
create type evidence_type as enum (
    'screenshot',
    'va_webhook',
    'mono_txn',
    'bank_alert',
    'chain_tx'
);
create type verdict_value as enum ('CONFIRMED', 'NOT_FOUND', 'SUSPICIOUS', 'UNVERIFIED');
create type decided_by as enum ('auto', 'seller');
create type fraud_kind as enum ('account_number', 'phone', 'device_hash', 'image_hash', 'name');
create type message_direction as enum ('in', 'out');

create table sellers (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    name text not null,
    business_name text not null,
    channel_ids jsonb not null default '{}'::jsonb,
    phone_hash text,
    default_language seller_language not null default 'en',
    virtual_account jsonb,
    settings jsonb not null default '{"auto_confirm": false, "reminder_hours": 24}'::jsonb,
    active boolean not null default true
);

create table products (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    seller_id uuid not null references sellers (id),
    name text not null,
    description text,
    price_kobo bigint not null check (price_kobo >= 0),
    currency text not null default 'NGN',
    stock integer not null default 0 check (stock >= 0),
    image_path text,
    tags text[] not null default '{}',
    embedding extensions.vector(1536),
    active boolean not null default true
);

create table buyers (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    channel text not null check (channel in ('whatsapp', 'instagram', 'messenger')),
    external_id text not null,
    display_name text,
    language seller_language,
    phone_hash text,
    first_seen_at timestamptz not null default now(),
    unique (channel, external_id)
);

create table orders (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    seller_id uuid not null references sellers (id),
    buyer_id uuid not null references buyers (id),
    ref text not null unique,
    items jsonb not null default '[]'::jsonb,
    total_kobo bigint not null check (total_kobo >= 0),
    status order_status not null default 'draft',
    reminder_count integer not null default 0 check (reminder_count >= 0),
    expires_at timestamptz
);

create table payments (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    order_id uuid not null references orders (id),
    method payment_method not null,
    expected_kobo bigint not null check (expected_kobo >= 0),
    status payment_status not null default 'pending',
    confirmed_at timestamptz
);

create table payment_evidence (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    payment_id uuid not null references payments (id),
    type evidence_type not null,
    source_id text not null,
    extracted jsonb,
    raw_path text,
    trust_level integer not null check (trust_level between 1 and 4),
    unique (type, source_id)
);

create table verdicts (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    payment_id uuid not null references payments (id),
    verdict verdict_value not null,
    confidence numeric,
    reasons text[] not null default '{}',
    jev_scores jsonb,
    rule_hits text[] not null default '{}',
    decided_by decided_by not null,
    release_allowed boolean not null default false
);

create table fraud_signals (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    kind fraud_kind not null,
    value_hash text not null,
    reported_by_seller_id uuid not null references sellers (id),
    evidence_id uuid references payment_evidence (id),
    severity integer not null check (severity between 1 and 3),
    confirmed boolean not null default false
);

create index fraud_signals_kind_value_hash_idx on fraud_signals (kind, value_hash);

create table messages (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    seller_id uuid not null references sellers (id),
    buyer_id uuid not null references buyers (id),
    channel text not null check (channel in ('whatsapp', 'instagram', 'messenger')),
    direction message_direction not null,
    external_msg_id text unique,
    type text not null,
    text text,
    media_path text,
    intent text,
    language seller_language,
    jev_scores jsonb
);

create table webhook_events (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    provider text not null,
    event_id text not null,
    payload jsonb not null,
    processed_at timestamptz,
    unique (provider, event_id)
);

create table daily_summaries (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    seller_id uuid not null references sellers (id),
    date date not null,
    orders integer not null default 0 check (orders >= 0),
    paid_kobo bigint not null default 0 check (paid_kobo >= 0),
    fakes_caught integer not null default 0 check (fakes_caught >= 0),
    naira_saved_kobo bigint not null default 0 check (naira_saved_kobo >= 0),
    unique (seller_id, date)
);

-- Service role used by the API bypasses RLS. No anon policies until the dashboard exists.
alter table sellers enable row level security;
alter table products enable row level security;
alter table buyers enable row level security;
alter table orders enable row level security;
alter table payments enable row level security;
alter table payment_evidence enable row level security;
alter table verdicts enable row level security;
alter table fraud_signals enable row level security;
alter table messages enable row level security;
alter table webhook_events enable row level security;
alter table daily_summaries enable row level security;
