-- Scheduler state and job logs for monitoring automation

create table public.scheduler_runs (
  id uuid primary key default gen_random_uuid(),
  job_type text not null check (job_type in ('ranking', 'signals', 'brief')),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  status text not null check (status in ('running', 'success', 'failed')) default 'running',
  error_message text,
  metadata jsonb default '{}'::jsonb,
  retries int not null default 0
);

create index scheduler_runs_job_type_idx on public.scheduler_runs (job_type, started_at desc);
create index scheduler_runs_status_idx on public.scheduler_runs (status, started_at desc);

-- Admin-only access to scheduler state
alter table public.scheduler_runs enable row level security;
revoke all on public.scheduler_runs from anon, authenticated;
grant select on public.scheduler_runs to authenticated;

create policy scheduler_runs_admin_only
  on public.scheduler_runs
  for select
  to authenticated
  using (
    exists (
      select 1
      from public.profiles
      where user_id = auth.uid()
        and role = 'admin'
        and active
    )
  );

-- Digest API tokens for external consumption
create table public.digest_tokens (
  token text primary key,
  description text,
  active boolean not null default true,
  created_at timestamptz not null default now(),
  last_used_at timestamptz
);

alter table public.digest_tokens enable row level security;
revoke all on public.digest_tokens from anon, authenticated;
