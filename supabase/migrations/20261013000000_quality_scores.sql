-- Agrega campos de calidad y métricas fundamentales adicionales a score_snapshots.

-- Agregar campo de calidad (score de 0-100 basado en métricas fundamentales)
alter table public.score_snapshots
  add column quality smallint,
  add constraint score_quality_range check (quality is null or quality between 0 and 100);

-- Agregar métricas fundamentales de calidad
alter table public.score_snapshots
  add column operating_margin numeric,
  add column net_margin numeric,
  add column roe numeric,
  add column debt_to_equity numeric,
  add column fcf_yield numeric;

-- Crear índice para búsquedas por calidad
create index score_snapshots_quality_idx on public.score_snapshots (quality desc) where quality is not null;

notify pgrst, 'reload schema';
