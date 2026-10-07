alter table public.score_snapshots
  add column calculated boolean not null default false;

notify pgrst, 'reload schema';
