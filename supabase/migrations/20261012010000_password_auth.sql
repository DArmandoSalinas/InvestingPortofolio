-- Sistema de autenticación con contraseñas

-- Agregar flag para obligar cambio de contraseña en primer login
alter table public.profiles
add column if not exists must_change_password boolean not null default false;

-- Tabla para tracking de invitaciones
create table if not exists public.invitations (
  email text primary key,
  temp_password text not null,
  invited_at timestamptz not null default now(),
  invited_by text,
  expires_at timestamptz not null default (now() + interval '7 days'),
  used_at timestamptz,
  constraint invitations_email_lowercase check (email = lower(email))
);

alter table public.invitations enable row level security;
revoke all on public.invitations from anon, authenticated;

comment on table public.invitations is 'Tracking de invitaciones con contraseñas temporales';
comment on column public.invitations.temp_password is 'Contraseña temporal legible (se borra después del primer login)';
