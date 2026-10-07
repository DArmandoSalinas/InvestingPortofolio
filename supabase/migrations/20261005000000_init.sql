-- Esquema de la Fase 1: acceso, empresas y snapshots de puntuación.

create table public.allowed_emails (
  email text primary key,
  role text not null check (role in ('admin', 'member')),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  constraint allowed_emails_lowercase check (email = lower(email))
);

create table public.profiles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  email text not null unique,
  display_name text,
  role text not null check (role in ('admin', 'member')),
  active boolean not null default true,
  created_at timestamptz not null default now(),
  constraint profiles_email_lowercase check (email = lower(email))
);

create table public.companies (
  id uuid primary key,
  market text not null check (market in ('us', 'mx')),
  symbol text not null,
  yahoo_symbol text not null,
  name text not null,
  sector text not null,
  currency text not null check (currency in ('USD', 'MXN')),
  universe_source text not null check (universe_source in ('sp500', 'ipc')),
  active boolean not null default true,
  unique (market, symbol)
);

create table public.score_snapshots (
  company_id uuid not null references public.companies (id),
  as_of date not null,
  growth smallint,
  value smallint,
  momentum smallint,
  composite smallint,
  value_reference text,
  revenue_growth_yoy numeric,
  earnings_growth_yoy numeric,
  pe numeric,
  ps numeric,
  ev_ebitda numeric,
  return_3m numeric,
  return_6m numeric,
  return_12m numeric,
  price_to_sma200 numeric,
  missing_fields text[] not null default '{}',
  na_fields text[] not null default '{}',
  primary key (company_id, as_of),
  constraint score_growth_range check (growth is null or growth between 0 and 100),
  constraint score_value_range check (value is null or value between 0 and 100),
  constraint score_momentum_range check (momentum is null or momentum between 0 and 100),
  constraint score_composite_range check (composite is null or composite between 0 and 100),
  constraint score_value_reference check (
    value_reference is null or value_reference in ('local', 'sp500_sector')
  ),
  constraint score_fields_disjoint check (not (missing_fields && na_fields)),
  constraint score_composite_rule check (
    (
      composite is null
      and (growth is null or value is null or momentum is null)
    )
    or (
      growth is not null
      and value is not null
      and momentum is not null
      and composite = (growth + value + momentum + 1) / 3
    )
  )
);

create index score_snapshots_as_of_idx on public.score_snapshots (as_of desc);

alter table public.allowed_emails enable row level security;
alter table public.profiles enable row level security;
alter table public.companies enable row level security;
alter table public.score_snapshots enable row level security;

revoke all on public.allowed_emails from anon, authenticated;
revoke all on public.companies from anon, authenticated;
revoke all on public.score_snapshots from anon, authenticated;
revoke all on public.profiles from anon, authenticated;
grant select on public.profiles to authenticated;

create policy profiles_select_own
  on public.profiles
  for select
  to authenticated
  using (auth.uid() = user_id);

create or replace function public.guard_allowed_email()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if not exists (
    select 1
    from public.allowed_emails
    where email = lower(new.email)
      and active
  ) then
    raise exception 'email_not_allowed';
  end if;
  return new;
end;
$$;

create trigger allowed_email_guard
  before insert on auth.users
  for each row
  execute function public.guard_allowed_email();

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  allowed_role text;
begin
  select role
  into allowed_role
  from public.allowed_emails
  where email = lower(new.email)
    and active;

  insert into public.profiles (user_id, email, display_name, role, active)
  values (
    new.id,
    lower(new.email),
    coalesce(new.raw_user_meta_data->>'full_name', split_part(new.email, '@', 1)),
    allowed_role,
    true
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row
  execute function public.handle_new_user();

revoke all on function public.guard_allowed_email() from public, anon, authenticated;
revoke all on function public.handle_new_user() from public, anon, authenticated;
