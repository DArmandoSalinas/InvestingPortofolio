-- Tabla para guardar métricas históricas de desempeño por tipo de señal.
-- Permite mostrar transparencia: "Esta regla tiene X% de acierto histórico"

create table public.signal_performance (
  setup text primary key check (setup in ('impulso', 'retroceso')),
  total_signals int not null default 0,
  targets int not null default 0,
  stops int not null default 0,
  expired int not null default 0,
  hit_rate numeric,
  avg_net_return numeric,
  avg_gross_return numeric,
  avg_winner numeric,
  avg_loser numeric,
  win_loss_ratio numeric,
  last_updated timestamptz not null default now(),
  constraint signal_performance_totals check (
    total_signals = targets + stops + expired
  )
);

-- Insertar filas iniciales para ambos tipos de señal
insert into public.signal_performance (setup, total_signals)
values ('impulso', 0), ('retroceso', 0);

-- Row level security
alter table public.signal_performance enable row level security;
revoke all on public.signal_performance from anon, authenticated;

notify pgrst, 'reload schema';
