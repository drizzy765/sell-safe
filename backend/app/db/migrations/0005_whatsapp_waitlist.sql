-- WhatsApp waitlist for sellers who want to be notified when WhatsApp becomes available
-- WhatsApp is currently locked (error 131031), this captures demand for when it unlocks

create table whatsapp_waitlist (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    phone_number text not null,  -- Nigerian format: +234XXXXXXXXXX
    notified_at timestamptz,      -- when we sent the "WhatsApp is ready" message
    connected_at timempotent       -- when they successfully connected
);

-- Unique constraint on phone number to prevent duplicates
create unique index whatsapp_waitlist_phone_number_idx on whatsapp_waitlist (phone_number);

-- Index for finding unnotified entries
create index whatsapp_waitlist_notified_at_idx on whatsapp_waitlist (notified_at) where notified_at is null;

-- Enable RLS
alter table whatsapp_waitlist enable row level security;

comment on table whatsapp_waitlist is 'Sellers waiting for WhatsApp to be unblocked. We notify them via WhatsApp when ready.';
comment on column whatsapp_waitlist.phone_number is 'Nigerian WhatsApp number in international format (+234XXXXXXXXXX)';
comment on column whatsapp_waitlist.notified_at is 'Timestamp when we sent the WhatsApp message saying WhatsApp is ready';
