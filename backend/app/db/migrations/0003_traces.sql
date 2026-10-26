-- Phase 3: trace persistence and speech metadata.

alter table messages
    add column if not exists transcript text,
    add column if not exists asr_confidence numeric;

comment on column messages.transcript is 'Raw STT output for audio messages; null for typed messages.';
comment on column messages.asr_confidence is ' recognizer confidence 0-1; null for typed messages or when absent.';

create table if not exists traces (
    id uuid primary key default gen_random_uuid(),
    created_at timestamptz not null default now(),
    trace_id text not null unique,
    seller_id uuid not null references sellers (id),
    buyer_id uuid not null references buyers (id),
    channel text not null,
    message_type text not null,
    intent text,
    language text,
    route_scores jsonb,
    order_ref text,
    tool_calls jsonb not null default '[]'::jsonb,
    reply text,
    steps integer not null default 0,
    errors text[] not null default '{}'
);

alter table traces enable row level security;
