create table public.morning_briefs (
  as_of date primary key,
  generated_at timestamptz not null default now(),
  headline text not null,
  ranking_as_of date,
  previous_as_of date,
  body jsonb not null,
  reading_ranking text not null default '',
  reading_signals text not null default '',
  reading_events text not null default ''
);

create table public.push_subscriptions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  endpoint text not null unique,
  p256dh text not null,
  auth text not null,
  created_at timestamptz not null default now()
);

alter table public.morning_briefs enable row level security;
alter table public.push_subscriptions enable row level security;
revoke all on public.morning_briefs from anon, authenticated;
revoke all on public.push_subscriptions from anon, authenticated;

notify pgrst, 'reload schema';
