create table public.investor_profiles (
  user_id uuid primary key references auth.users (id) on delete cascade,
  currency text not null check (currency in ('MXN', 'USD')),
  amount numeric not null check (amount > 0),
  monthly_contribution numeric not null check (monthly_contribution >= 0),
  horizon_years int not null check (horizon_years between 1 and 40),
  goal text not null check (goal in ('preservar', 'crecer', 'ingreso')),
  risk text not null check (risk in ('bajo', 'medio', 'alto')),
  proposal jsonb,
  updated_at timestamptz not null default now()
);

create table public.holdings (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references auth.users (id) on delete cascade,
  asset_class text not null check (asset_class in ('stock', 'etf', 'crypto', 'cetes', 'ahorro')),
  symbol text not null,
  name text not null,
  yahoo_symbol text,
  quantity numeric not null check (quantity > 0),
  unit_cost numeric not null check (unit_cost > 0),
  currency text not null check (currency in ('MXN', 'USD')),
  opened_on date not null,
  unique (user_id, asset_class, symbol)
);

alter table public.investor_profiles enable row level security;
alter table public.holdings enable row level security;
revoke all on public.investor_profiles from anon, authenticated;
revoke all on public.holdings from anon, authenticated;

notify pgrst, 'reload schema';
