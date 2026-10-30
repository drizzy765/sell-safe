-- Direct USDC payments on Base. tx_hash is unique so one hash cannot pay two orders.
-- amount is integer USDC base units (6 decimals), not kobo.

create table crypto_payments (
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

create index crypto_payments_order_id_idx on crypto_payments (order_id);

alter table crypto_payments enable row level security;

comment on table crypto_payments is
    'On-chain USDC checks. amount is USDC base units (6 decimals), not naira kobo.';
comment on column crypto_payments.tx_hash is
    'Transaction hash. Unique so a reused hash cannot confirm a second order.';
comment on column crypto_payments.from_address is 'ERC-20 Transfer sender.';
comment on column crypto_payments.to_address is 'ERC-20 Transfer recipient. Must be the seller wallet.';
comment on column crypto_payments.status is
    'CONFIRMED, PENDING (waiting for confirmations), or SUSPICIOUS.';
