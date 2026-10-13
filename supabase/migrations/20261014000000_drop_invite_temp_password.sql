-- La contraseña temporal solo se muestra una vez en Acceso (cookie flash) y
-- vive hasheada en Supabase Auth. No se guarda en texto plano en invitations.

alter table public.invitations
  drop column if exists temp_password;

comment on table public.invitations is
  'Tracking de invitaciones. La contraseña temporal no se almacena aquí; solo en Supabase Auth.';
