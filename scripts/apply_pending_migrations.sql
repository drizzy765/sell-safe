-- Apply in Supabase SQL editor if missing.
-- Pending as of smoke check: whatsapp_waitlist (0005) and crypto_payments (0006).

-- 0005_whatsapp_waitlist.sql
create table if not exists whatsapp_waitlist (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    phone_number text not null check (phone_number ~ '^\+234[0-9]{10}$'),
    notified_at timestamptz
);

create unique index if not exists whatsapp_waitlist_phone_number_idx on whatsapp_waitlist (phone_number);

create index if not exists whatsapp_waitlist_notified_at_idx on whatsapp_waitlist (notified_at)
    where notified_at is null;

alter table whatsapp_waitlist enable row level security;

comment on table whatsapp_waitlist is
    'Sellers waiting for WhatsApp to unblock. The number is stored so we can message them.';
comment on column whatsapp_waitlist.phone_number is
    'Nigerian WhatsApp number in international format (+234 and 10 digits).';
comment on column whatsapp_waitlist.notified_at is
    'Timestamp when we sent the WhatsApp message saying WhatsApp is ready.';

-- 0006_crypto_payments.sql
create table if not exists crypto_payments (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    order_id uuid not null references orders (id),
    tx_hash text not null,
    network text not null,
    from_address text,
    to_address text,
    amount bigint,
    confirmations integer,
    status text not null check (status in ('CONFIRMED', 'PENDING', 'SUSPICIOUS')),
    reason text,
    checked_at timestamptz not null default now(),
    unique (tx_hash)
);

create index if not exists crypto_payments_order_id_idx on crypto_payments (order_id);

alter table crypto_payments enable row level security;

comment on table crypto_payments is
    'On-chain USDC checks. amount is USDC base units (6 decimals), not naira kobo.';
comment on column crypto_payments.tx_hash is
    'Transaction hash. Unique so a reused hash cannot confirm a second order.';
comment on column crypto_payments.from_address is 'ERC-20 Transfer sender.';
comment on column crypto_payments.to_address is 'ERC-20 Transfer recipient. Must be the seller wallet.';
comment on column crypto_payments.status is
    'CONFIRMED, PENDING (waiting for confirmations), or SUSPICIOUS.';
