# Railway Infrastructure as Code

Este directorio sustituye el antiguo `railway.json` / `railway.toml` (Config as Code), que deja de leerse el **2026-12-01**.

## Uso

1. Instala el CLI reciente y el SDK: `npm install` en la raíz del monorepo.
2. `railway link` al proyecto del backend.
3. `railway config plan` / `railway config apply` para sincronizar.

Las variables secretas (`SUPABASE_*`, `ADMIN_EMAIL`, SMTP, etc.) se configuran en el dashboard de Railway o con `preserve()` — nunca en este archivo.
