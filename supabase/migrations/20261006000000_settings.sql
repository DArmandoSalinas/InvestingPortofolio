create table public.signal_config (
  id int primary key default 1 check (id = 1),
  stock_commission numeric not null check (stock_commission >= 0 and stock_commission <= 0.05),
  crypto_commission numeric not null check (crypto_commission >= 0 and crypto_commission <= 0.05),
  horizon_sessions int not null check (horizon_sessions between 1 and 30)
);

insert into public.signal_config (id, stock_commission, crypto_commission, horizon_sessions)
values (1, 0.001, 0.002, 10);

create table public.watchlist (
  yahoo_symbol text primary key,
  symbol text not null,
  name text not null,
  asset_class text not null check (asset_class in ('stock', 'crypto')),
  active boolean not null default true
);

insert into public.watchlist (yahoo_symbol, symbol, name, asset_class) values
  ('AAPL', 'AAPL', 'Apple', 'stock'),
  ('MSFT', 'MSFT', 'Microsoft', 'stock'),
  ('NVDA', 'NVDA', 'NVIDIA', 'stock'),
  ('AMZN', 'AMZN', 'Amazon', 'stock'),
  ('META', 'META', 'Meta', 'stock'),
  ('GOOGL', 'GOOGL', 'Alphabet', 'stock'),
  ('AVGO', 'AVGO', 'Broadcom', 'stock'),
  ('TSLA', 'TSLA', 'Tesla', 'stock'),
  ('AMD', 'AMD', 'AMD', 'stock'),
  ('NFLX', 'NFLX', 'Netflix', 'stock'),
  ('JPM', 'JPM', 'JPMorgan', 'stock'),
  ('LLY', 'LLY', 'Eli Lilly', 'stock'),
  ('XOM', 'XOM', 'Exxon Mobil', 'stock'),
  ('COST', 'COST', 'Costco', 'stock'),
  ('WMT', 'WMT', 'Walmart', 'stock'),
  ('BTC-USD', 'BTC', 'Bitcoin', 'crypto'),
  ('ETH-USD', 'ETH', 'Ethereum', 'crypto');

alter table public.signal_config enable row level security;
alter table public.watchlist enable row level security;
revoke all on public.signal_config from anon, authenticated;
revoke all on public.watchlist from anon, authenticated;

notify pgrst, 'reload schema';
