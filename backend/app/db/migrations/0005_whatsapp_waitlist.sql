-- WhatsApp waitlist for sellers who want a message when WhatsApp unblocks (error 131031).

create table whatsapp_waitlist (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    phone_number text not null check (phone_number ~ '^\+234[0-9]{10}$'),
    notified_at timestamptz
);

create unique index whatsapp_waitlist_phone_number_idx on whatsapp_waitlist (phone_number);

create index whatsapp_waitlist_notified_at_idx on whatsapp_waitlist (notified_at)
    where notified_at is null;

alter table whatsapp_waitlist enable row level security;

comment on table whatsapp_waitlist is
    'Sellers waiting for WhatsApp to unblock. The number is stored so we can message them.';
comment on column whatsapp_waitlist.phone_number is
    'Nigerian WhatsApp number in international format (+234 and 10 digits).';
comment on column whatsapp_waitlist.notified_at is
    'Timestamp when we sent the WhatsApp message saying WhatsApp is ready.';
