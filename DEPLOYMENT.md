# Guía de Despliegue

Esta guía describe cómo desplegar la plataforma en producción usando Vercel (frontend) y Railway o Render (backend).

## Prerequisitos

1. Cuenta en [Supabase](https://supabase.com) (crea un proyecto nuevo)
2. Cuenta en [Vercel](https://vercel.com)
3. Cuenta en [Railway](https://railway.app) o [Render](https://render.com)
4. Cuenta en [xAI](https://console.x.ai) para obtener API key de Grok
5. (Opcional) Servicio SMTP para correos (ej: SendGrid, Mailgun, o SMTP de Gmail)

## 1. Configurar Supabase

1. Crea un proyecto nuevo en Supabase
2. Ve a Settings → API y copia:
   - Project URL
   - anon public key
   - service_role key (guárdala de forma segura, nunca la expongas al cliente)
3. Ve a SQL Editor y ejecuta las migraciones en orden:
   ```bash
   # Desde tu computadora local, con Supabase CLI instalado:
   npx supabase link --project-ref tu-proyecto-ref
   npx supabase db push
   ```
   O copia y ejecuta manualmente cada archivo de `supabase/migrations/` en orden.

4. Ve a Authentication → Providers:
   - Activa "Email" (magic link)
   - (Opcional) Activa "Google" si deseas login con Google
     - Necesitarás crear OAuth credentials en Google Cloud Console
     - Agrega las URIs de callback de Supabase

## 2. Desplegar el Backend (FastAPI) en Railway

El repositorio incluye configuración automática para Railway (`Procfile` y `nixpacks.toml`).

### Opción A: Railway

1. Ve a [Railway](https://railway.app) y crea un nuevo proyecto
2. Agrega un nuevo servicio desde tu repositorio de GitHub
3. Railway detectará automáticamente la configuración (`nixpacks.toml` y `Procfile`)
4. Configura las variables de entorno en Railway:
   ```
   SUPABASE_URL=https://tu-proyecto.supabase.co
   SUPABASE_SERVICE_ROLE_KEY=tu-service-role-key-secreto
   SUPABASE_ANON_KEY=tu-anon-key-publico
   ADMIN_EMAIL=tu-email@dominio.com
   RANK_HIGHLIGHT_MIN=70
   CORS_ORIGINS=https://tu-dominio.vercel.app
   XAI_API_KEY=tu-xai-api-key
   SITE_URL=https://tu-dominio.vercel.app
   ```

4. Configura VAPID keys para notificaciones push:
   ```bash
   # En tu computadora local:
   npx web-push generate-vapid-keys
   ```
   Agrega las keys generadas a Railway:
   ```
   VAPID_PUBLIC_KEY=la-key-publica-generada
   VAPID_PRIVATE_KEY=la-key-privada-generada
   VAPID_SUBJECT=mailto:tu-email@dominio.com
   ```

5. (Opcional) Si tienes SMTP configurado:
   ```
   SMTP_HOST=smtp.sendgrid.net
   SMTP_PORT=587
   SMTP_USER=apikey
   SMTP_PASSWORD=tu-sendgrid-api-key
   SMTP_FROM=notificaciones@tu-dominio.com
   ```

6. Railway desplegará automáticamente usando la configuración en `nixpacks.toml`

7. Anota la URL pública que Railway asigna (ej: `https://tu-app.up.railway.app`)

### Opción B: Render

1. Ve a [Render](https://render.com) y crea un nuevo Web Service
2. Conecta tu repositorio de GitHub
3. Configuración:
   - Name: `plataforma-inversion-api`
   - Root Directory: `apps/api`
   - Build Command: `pip install uv && uv sync`
   - Start Command: `uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Plan: Starter (o Free para pruebas)

4. Agrega las mismas variables de entorno que en Railway
5. Anota la URL pública (ej: `https://plataforma-inversion-api.onrender.com`)

## 3. Desplegar el Frontend (Next.js) en Vercel

1. Ve a [Vercel](https://vercel.com) e importa tu repositorio
2. En Project Settings:
   - Framework Preset: Next.js
   - Root Directory: `apps/web`
   - Build Command: `npm run build`
   - Output Directory: `.next`

3. Configura las variables de entorno en Vercel:
   ```
   NEXT_PUBLIC_SUPABASE_URL=https://tu-proyecto.supabase.co
   NEXT_PUBLIC_SUPABASE_ANON_KEY=tu-anon-key-publico
   NEXT_PUBLIC_API_URL=https://tu-api.railway.app
   NEXT_PUBLIC_SITE_URL=https://tu-dominio.vercel.app
   ```

4. Despliega. Vercel te asignará un dominio (ej: `tu-app.vercel.app`)

5. (Opcional) Configura un dominio personalizado en Vercel Settings

## 4. Configurar el Primer Admin

1. En la API, el email en `ADMIN_EMAIL` será el administrador inicial
2. Ve a tu sitio web y haz clic en "Iniciar sesión"
3. Ingresa el email de admin y recibirás un magic link
4. Una vez dentro, ve a "Acceso" y agrega usuarios adicionales

## 5. Crear Token para el Digest API

El endpoint `/api/v1/digest` requiere autenticación por token. Para crear un token:

1. Conecta a tu base de datos Supabase con SQL Editor
2. Ejecuta:
   ```sql
   insert into public.digest_tokens (token, description, active)
   values ('tu-token-secreto-aleatorio', 'Token para asistente externo', true);
   ```

3. Úsalo así:
   ```bash
   curl "https://tu-api.railway.app/api/v1/digest?token=tu-token-secreto-aleatorio"
   ```

## 6. Verificar que Todo Funciona

1. **Frontend**: Abre tu dominio en Vercel, inicia sesión
2. **Ranking**: Debería mostrar "Datos de ejemplo" hasta que corra el primer cálculo
3. **Backend logs**: En Railway/Render, revisa los logs:
   - Debería mostrar "ciclo de actualización iniciado"
   - Cada 30 minutos intenta calcular el ranking del día
   - A las 9:00 AM (New York) genera el resumen matutino

4. **Forzar cálculo** (opcional):
   ```bash
   # SSH a Railway o usar Render shell:
   uv run python -m app.refresh_ranking
   ```

## 7. Automatización con GitHub Actions (Alternativa)

Si prefieres que las tareas programadas corran en GitHub Actions en lugar de en el servidor:

1. Deshabilita el ciclo automático en `main.py` (comenta la línea del `refresh_loop`)
2. Crea `.github/workflows/scheduled-tasks.yml`:
   ```yaml
   name: Scheduled Tasks
   
   on:
     schedule:
       # Corre cada hora
       - cron: '0 * * * *'
     workflow_dispatch:
   
   jobs:
     refresh:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.12'
         - uses: astral-sh/setup-uv@v5
         - name: Install dependencies
           working-directory: ./apps/api
           run: uv sync
         - name: Run refresh
           working-directory: ./apps/api
           run: uv run python -m app.refresh_ranking
           env:
             SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
             SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}
             SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}
             ADMIN_EMAIL: ${{ secrets.ADMIN_EMAIL }}
             XAI_API_KEY: ${{ secrets.XAI_API_KEY }}
             # ... resto de variables
   ```

3. Agrega todos los secretos necesarios en GitHub Settings → Secrets and variables → Actions

**Ventaja**: No depende de un servidor siempre encendido  
**Desventaja**: Cron de GitHub Actions puede tener +/- 15 min de variación

## 8. Monitoreo

- **Railway**: Dashboard muestra logs en tiempo real, uso de CPU/memoria, crashes
- **Render**: Logs y métricas en el dashboard, email alerts para crashes
- **Vercel**: Analytics y logs de edge functions
- **Supabase**: Dashboard → API → Logs muestra todas las queries

## Costos Estimados (a partir de 2024)

- **Supabase**: Free tier hasta 500MB, luego $25/mes (Pro)
- **Railway**: $5/mes de crédito gratis, luego ~$5-20/mes según uso
- **Render**: Free tier con limitaciones, $7/mes (Starter)
- **Vercel**: Free tier generoso, Pro $20/mes si necesitas más
- **xAI (Grok)**: Consulta pricing actualizado en console.x.ai

**Total**: Puedes empezar gratis o con ~$10-20/mes usando tiers de pago básicos.

## Troubleshooting

### El ranking no se calcula automáticamente
- Revisa los logs del backend: debería decir "ciclo de actualización iniciado"
- Verifica que `SUPABASE_SERVICE_ROLE_KEY` sea correcta y tenga permisos de escritura
- El ranking se calcula solo UNA VEZ al día (por la mañana en Monterrey)

### Grok no responde
- Verifica que `XAI_API_KEY` sea válida: `curl -H "Authorization: Bearer tu-key" https://api.x.ai/v1/models`
- Revisa los logs: pueden haber errores 401 (key inválida) o 429 (rate limit)

### Correos no se envían
- Si no configuras SMTP, los correos se "envían" pero no llegan a nadie
- En desarrollo usa Mailpit (local)
- En producción necesitas SMTP real o un servicio como SendGrid

### La API no puede escribir en Supabase
- Verifica que uses `SUPABASE_SERVICE_ROLE_KEY`, no la anon key
- Revisa las Row Level Security policies en Supabase

### Errores 404 para símbolos mexicanos
- Algunos símbolos de Wikipedia pueden estar dados de baja en Yahoo Finance
- La plataforma los omite automáticamente (ej: ELEKTRA.MX, ALFAA.MX)
- Si aparecen otros símbolos problemáticos, agrégalos a `DELISTED_SYMBOLS` en `apps/api/app/market_data.py`

## Soporte

Para problemas técnicos:
1. Revisa los logs del servicio correspondiente
2. Verifica que todas las variables de entorno estén configuradas
3. Prueba las migraciones de base de datos

---

¡Listo! Con esto tu plataforma debería estar corriendo 24/7 en producción.
