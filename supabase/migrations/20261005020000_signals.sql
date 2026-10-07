create table public.signals (
  id uuid primary key default gen_random_uuid(),
  as_of date not null,
  asset_class text not null check (asset_class in ('stock', 'crypto')),
  symbol text not null,
  yahoo_symbol text not null,
  name text not null,
  setup text not null check (setup in ('impulso', 'retroceso')),
  entry numeric not null,
  stop numeric not null,
  target numeric not null,
  confidence smallint not null check (confidence between 0 and 100),
  reasons text[] not null,
  risks text[] not null,
  horizon_sessions int not null,
  commission_rate numeric not null,
  status text not null check (status in ('open', 'target', 'stop', 'expired')),
  exit_price numeric,
  exit_as_of date,
  gross_return numeric,
  net_return numeric,
  spy_return numeric,
  btc_return numeric,
  context_note text not null default '',
  unique (yahoo_symbol, setup, as_of),
  constraint signal_levels check (stop < entry and entry < target)
);

create index signals_status_idx on public.signals (status);

alter table public.signals enable row level security;
revoke all on public.signals from anon, authenticated;

notify pgrst, 'reload schema';
