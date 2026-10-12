# Resumen de Implementación: Autenticación con Invitación y Contraseña

## PR Creado
**Branch:** `cursor/invitation-password-auth-d80a`
**Link:** https://github.com/DArmandoSalinas/InvestingPortofolio/pull/new/cursor/invitation-password-auth-d80a

⚠️ **NO hacer merge todavía** - Diego debe probar el flujo real en el preview de Vercel primero.

---

## ✅ Cambios Implementados

### 1. Backend (FastAPI)
- **`apps/api/app/mailer.py`**: 
  - Reemplazada función `signin_link()` con `invite_user()` que usa la Admin API de Supabase (`/auth/v1/invite`)
  - El correo lo envía Supabase con su SMTP configurado (Gmail en producción)
  - Redirect a `/auth/confirm?next=/bienvenida` para flujo token_hash
  - `send_invitation()` retorna `"smtp"` o `"supabase"` según configuración

- **`apps/api/app/main.py`**:
  - Actualizado endpoint `/admin/access` (crear invitación) para usar `send_invitation()`
  - Actualizado endpoint `/admin/access/link` (reenviar) para usar `send_invitation()`
  - Eliminada actualización de perfil en el momento de invitación (Supabase lo maneja con el trigger)

- **`apps/api/tests/test_auth.py`**: 
  - Tests unitarios para `invite_user()`, `send_invitation()` y manejo de errores
  - Mock de httpx para simular Admin API
  - 8 tests nuevos, todos pasan ✓

### 2. Frontend (Next.js)

#### Nuevas páginas:
- **`apps/web/src/app/bienvenida/page.tsx`**: 
  - Página para establecer contraseña después de invitación o reset
  - Dos campos de contraseña con confirmación
  - Requisitos visibles: mínimo 8 caracteres
  - Mensajes de error claros en español
  
- **`apps/web/src/app/bienvenida/actions.ts`**: 
  - Validación de contraseña (mínimo 8 caracteres, coincidencia)
  - Usa `supabase.auth.updateUser({ password })` (API nativa)
  - Redirect a `/` después de establecer contraseña

- **`apps/web/src/app/auth/confirm/route.ts`**: 
  - Nuevo endpoint para flujo token_hash/verifyOtp
  - Maneja `invite`, `recovery` y `magiclink`
  - Funciona en cualquier navegador (no depende de PKCE)
  - Parámetro `next` para redirect post-auth

#### Actualizaciones:
- **`apps/web/src/app/login/page.tsx`**:
  - **Principal**: Correo + Contraseña con `signInWithPassword`
  - **"¿Olvidaste tu contraseña?"**: Form separado que toma el email y usa `resetPasswordForEmail`
  - **Secundario**: Enlace mágico en `<details>` ("Otras opciones")
  - Google OAuth eliminado (no está configurado)
  - Mensajes de error claros en español

- **`apps/web/src/app/login/actions.ts`**:
  - `signInWithPassword()`: Auth principal
  - `resetPassword()`: Envía email con link a `/bienvenida`
  - `sendLink()`: Enlace mágico opcional
  - Manejo de errores específicos (credenciales, invitación, revocación)

- **`apps/web/src/app/auth/callback/route.ts`**:
  - Soporte para parámetro `?next=` 
  - Redirect configurable post-auth

#### Responsive y UI:
- **`apps/web/src/components/highlights.tsx`**:
  - ✅ Cambio de "C 100 · V 95 · M 75" a "Crecimiento 100 · Valor 95 · Momentum 75"
  - ✅ Reemplazado flex con grid responsive: 1 columna móvil, 2-4 columnas según tamaño
  - ✅ Header con flex-col en móvil para evitar amontonamiento del título
  - ✅ Título "70 puntos o más en cada una" ahora legible en móvil
  - ✅ Sin scroll horizontal a 360px

- **`apps/web/src/components/shell.tsx`**:
  - Padding responsivo: `px-4 sm:px-8 lg:px-12`
  - Header con wrap y gaps adaptivos
  - Email y botón Salir con wrap

- **`apps/web/src/components/nav-links.tsx`**:
  - Navigation con flex-wrap
  - Gaps reducidos en móvil: `gap-3 sm:gap-5`

- **`apps/web/src/components/ranking-table.tsx`**:
  - Tabla con `overflow-x-auto` contenido
  - Scroll horizontal controlado solo en la tabla

- **`apps/web/src/app/(studio)/page.tsx`**:
  - Títulos responsivos: `text-4xl sm:text-5xl`

- **`apps/web/src/app/login/page.tsx` y `/bienvenida/page.tsx`**:
  - Padding móvil: `px-4 sm:px-8`
  - Títulos adaptivos

### 3. Deployment (Railway)
- **`Dockerfile`**:
  ```dockerfile
  FROM python:3.12-slim
  # Instala uv desde ghcr.io/astral-sh/uv
  # Copia pyproject.toml, uv.lock, .python-version
  # uv sync --frozen --no-dev
  # Copia apps/api/app
  # HEALTHCHECK /health
  # CMD uvicorn app.main:app --host 0.0.0.0 --port 8000
  ```

- **`railway.json`**:
  ```json
  {
    "build": { "builder": "DOCKERFILE" },
    "deploy": {
      "startCommand": "uv run uvicorn app.main:app --host 0.0.0.0 --port $PORT",
      "healthcheckPath": "/health",
      "restartPolicyType": "ON_FAILURE"
    }
  }
  ```

---

## 🗄️ Migraciones

**NO se requieren nuevas migraciones.**

Las migraciones existentes ya soportan el flujo:
- `20261005000000_init.sql`: Tabla `allowed_emails`, trigger `allowed_email_guard`, función `handle_new_user()`
- Estas siguen funcionando igual: la lista blanca se valida antes de crear el usuario

**Notas:**
- No había tabla `invitations` ni `temp_password` que borrar (nunca existieron en producción)
- No había archivos `REPORTE_FINAL.md` ni `PENDING_PASSWORD_AUTH.md` que limpiar

---

## 📧 Plantillas de Correo de Supabase

**⚠️ IMPORTANTE:** Debes actualizar 3 plantillas en Supabase para que usen `{{ .TokenHash }}` en lugar de `{{ .Token }}`.

Ver archivo completo: **`PLANTILLAS_EMAIL_SUPABASE.md`**

### Resumen:
1. **Invite user**: `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=invite&next=/bienvenida`
2. **Reset password**: `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=recovery&next=/bienvenida`
3. **Magic Link**: `{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=magiclink`

**Por qué `token_hash`:**
- Funciona en cualquier navegador (aunque se abra en Gmail app o navegador diferente)
- No depende de PKCE que falla cross-browser
- Usa `verifyOtp` que es el flujo recomendado por Supabase para SSR

**Aplicar:** Authentication → Email Templates en el dashboard de Supabase

---

## 🔐 Variables de Entorno

**No se requieren nuevas variables.**

Las existentes siguen funcionando:
- Backend: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SITE_URL`, `SMTP_*` (Gmail ya configurado en prod)
- Frontend: `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_SITE_URL`

**Nota sobre Vercel Preview:**
- Ya permitiste las URLs de preview en Supabase (lista blanca de redirects)
- El preview creará una URL tipo `https://investing-portfolio-*.vercel.app`

---

## 🚀 Pasos para el Primer Login de Diego

### Opción A: Flujo de Invitación (Recomendado)
1. **Tú (admin):**
   - Entra a `/admin/acceso` en producción
   - Agrega el correo de Diego con rol "Miembro" o "Admin"
   - El sistema llama a Supabase Admin API → Supabase envía el correo con Gmail

2. **Diego:**
   - Revisa su correo (bandeja de entrada o spam)
   - Hace clic en el enlace: `...auth/confirm?token_hash=...&type=invite&next=/bienvenida`
   - Llega a `/bienvenida`
   - Escribe su contraseña dos veces (mínimo 8 caracteres)
   - Presiona "Establecer contraseña"
   - Entra a la app

3. **Próximos accesos de Diego:**
   - Va a `/login`
   - Ingresa su correo y contraseña
   - Presiona "Iniciar sesión"
   - Entra directo

### Opción B: Ya tiene una cuenta pero olvidó su contraseña
1. **Diego:**
   - Va a `/login`
   - Hace clic en "¿Olvidaste tu contraseña?"
   - Ingresa su correo y presiona "Enviar"
   - Revisa su correo
   - Hace clic en el enlace de restablecimiento
   - Llega a `/bienvenida`
   - Establece nueva contraseña
   - Entra a la app

---

## 🧪 Testing

### Backend
```bash
cd apps/api
uv run pytest
# ✓ 55 tests pass (incluyendo 8 nuevos de auth)
```

### Frontend
```bash
cd apps/web
npm run build
# ✓ Build exitoso, TypeScript sin errores
# ✓ Todas las rutas generadas correctamente
```

### CI/CD
- El PR disparará GitHub Actions (si están configurados)
- Vercel creará preview automático
- Las URLs de preview ya están permitidas en Supabase

---

## 📝 Checklist Final

Antes de hacer merge:

- [ ] Verificar que Vercel creó el preview del PR
- [ ] Actualizar las 3 plantillas de correo en Supabase (ver `PLANTILLAS_EMAIL_SUPABASE.md`)
- [ ] Probar flujo completo en el preview:
  - [ ] Agregar un correo en `/admin/acceso` del preview
  - [ ] Verificar que llega el correo de invitación
  - [ ] Abrir el link en un navegador diferente (probar cross-browser)
  - [ ] Establecer contraseña en `/bienvenida`
  - [ ] Salir y volver a entrar con correo + contraseña
  - [ ] Probar "¿Olvidaste tu contraseña?" (reset)
  - [ ] Verificar responsive en móvil (360px): sin scroll horizontal en Altas en los tres
- [ ] Verificar que CI pasa (tests, lint, build)
- [ ] Hacer merge a `main`
- [ ] Desplegar a producción (Vercel auto-deploy, Railway con el nuevo Dockerfile)
- [ ] Invitar a Diego en producción

---

## 🔍 Cambios Visuales Incluidos

1. **Tarjetas "Altas en los tres":**
   - Antes: `C 100 · V 95 · M 75`
   - Ahora: `Crecimiento 100 · Valor 95 · Momentum 75`

2. **Layout móvil (~360px):**
   - Título y texto "70 puntos o más en cada una" ya no se amontonan
   - Grid responsive: 1 columna móvil, 2-4 según tamaño de pantalla
   - Sin scroll horizontal en ninguna página
   - Padding y tipografía adaptivos

3. **Otras mejoras:**
   - Navigation con wrap
   - Tabla de ranking con scroll controlado
   - Login y Bienvenida responsive

---

## 📦 Archivos del PR

### Nuevos:
- `Dockerfile`
- `railway.json`
- `apps/api/tests/test_auth.py`
- `apps/web/src/app/bienvenida/page.tsx`
- `apps/web/src/app/bienvenida/actions.ts`
- `apps/web/src/app/auth/confirm/route.ts`
- `PLANTILLAS_EMAIL_SUPABASE.md` (documentación)
- `RESUMEN_IMPLEMENTACION.md` (este archivo)

### Modificados:
- `apps/api/app/mailer.py`
- `apps/api/app/main.py`
- `apps/web/src/app/login/page.tsx`
- `apps/web/src/app/login/actions.ts`
- `apps/web/src/app/auth/callback/route.ts`
- `apps/web/src/app/(studio)/layout.tsx`
- `apps/web/src/app/(studio)/page.tsx`
- `apps/web/src/components/highlights.tsx`
- `apps/web/src/components/nav-links.tsx`
- `apps/web/src/components/ranking-table.tsx`
- `apps/web/src/components/shell.tsx`

### Eliminados:
- Ninguno (no había archivos de password auth previos)

---

## 🎯 Próximos Pasos Sugeridos (Post-Merge)

1. Monitorear el flujo de invitaciones en producción
2. Configurar Google OAuth si lo necesitan más adelante
3. Considerar agregar 2FA o límites de intentos de login
4. Agregar logs de autenticación en el backend para debugging

---

**Fecha de implementación:** 12 de octubre de 2026
**Autor:** Cursor Agent (Cloud)
