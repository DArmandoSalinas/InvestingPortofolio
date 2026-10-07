alter table public.morning_briefs
  add column if not exists emailed_at timestamptz;

notify pgrst, 'reload schema';
