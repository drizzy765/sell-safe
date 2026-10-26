-- Pending product photos. A product row is inserted only after the seller confirms a price.
-- At most one pending draft per seller and buyer.

create table catalog_drafts (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    seller_id uuid not null references sellers (id),
    buyer_id uuid not null references buyers (id),
    image_path text not null,
    extraction jsonb,
    status text not null default 'pending' check (status in ('pending', 'saved'))
);

create unique index catalog_drafts_one_pending
    on catalog_drafts (seller_id, buyer_id)
    where status = 'pending';

alter table catalog_drafts enable row level security;
