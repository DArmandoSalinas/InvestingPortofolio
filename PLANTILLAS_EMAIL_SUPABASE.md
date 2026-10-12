# Plantillas de correo de Supabase a actualizar

Para que el flujo de autenticación funcione correctamente con token_hash/verifyOtp, debes actualizar las siguientes plantillas de correo en Supabase (Authentication → Email Templates) o mediante la Management API.

## 1. Invite user (Invitación)

**Cuándo se usa:** Cuando el admin agrega un correo en /admin/acceso

**Asunto:** Invitación a Inversión

**Contenido HTML:**
```html
<h2>Bienvenido a Inversión</h2>

<p>Has sido invitado a unirte a la plataforma de inversión.</p>

<p>Haz clic en el siguiente enlace para establecer tu contraseña y acceder:</p>

<p><a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=invite&next=/bienvenida">Establecer mi contraseña</a></p>

<p>Este enlace caduca en 24 horas.</p>

<p>Si no solicitaste esta invitación, ignora este mensaje.</p>

<hr />

<p style="color: #8e8e93; font-size: 12px;">
  Inversión – Plataforma privada de análisis. El contenido es informativo, no es asesoría financiera.
</p>
```

## 2. Reset password (Restablecer contraseña)

**Cuándo se usa:** Cuando un usuario hace clic en "¿Olvidaste tu contraseña?" en /login

**Asunto:** Restablece tu contraseña de Inversión

**Contenido HTML:**
```html
<h2>Restablece tu contraseña</h2>

<p>Recibimos una solicitud para restablecer la contraseña de tu cuenta.</p>

<p>Haz clic en el siguiente enlace para crear una nueva contraseña:</p>

<p><a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=recovery&next=/bienvenida">Restablecer mi contraseña</a></p>

<p>Este enlace caduca en 1 hora.</p>

<p>Si no solicitaste restablecer tu contraseña, ignora este mensaje.</p>

<hr />

<p style="color: #8e8e93; font-size: 12px;">
  Inversión – Plataforma privada de análisis. El contenido es informativo, no es asesoría financiera.
</p>
```

## 3. Magic Link (Enlace mágico) - Opcional

**Cuándo se usa:** Cuando un usuario usa la opción "Otras opciones de inicio de sesión" → "Enviar enlace mágico" en /login

**Asunto:** Tu enlace para entrar a Inversión

**Contenido HTML:**
```html
<h2>Accede a tu cuenta</h2>

<p>Usa este enlace para entrar a Inversión:</p>

<p><a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=magiclink">Entrar a mi cuenta</a></p>

<p>Este enlace caduca en 1 hora.</p>

<p>Si no pediste entrar, ignora este mensaje.</p>

<hr />

<p style="color: #8e8e93; font-size: 12px;">
  Inversión – Plataforma privada de análisis. El contenido es informativo, no es asesoría financiera.
</p>
```

## Nota importante sobre {{ .TokenHash }}

El cambio clave es usar `{{ .TokenHash }}` en lugar de `{{ .Token }}` o `{{ .ConfirmationURL }}`. 

**Por qué:**
- El flujo con `token_hash` funciona en cualquier navegador, incluso si el usuario abre el enlace en un navegador diferente o en la app de Gmail
- El flujo PKCE anterior con `code` fallaba si se abría en un contexto diferente
- La ruta `/auth/confirm` usa `verifyOtp` que maneja correctamente el `token_hash`

## Aplicar las plantillas

### Opción A: Manual en el Dashboard de Supabase
1. Ve a tu proyecto en https://supabase.com/dashboard
2. Authentication → Email Templates
3. Edita cada plantilla y pega el HTML correspondiente
4. Guarda los cambios

### Opción B: Management API (automatizado)
```bash
# Requiere tu Management API token de Supabase
curl -X PATCH \
  https://api.supabase.com/v1/projects/{project-ref}/config/auth \
  -H "Authorization: Bearer {management-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "MAILER_TEMPLATES": {
      "invite": {
        "subject": "Invitación a Inversión",
        "content": "... HTML de arriba ..."
      },
      "recovery": {
        "subject": "Restablece tu contraseña de Inversión",
        "content": "... HTML de arriba ..."
      },
      "magic_link": {
        "subject": "Tu enlace para entrar a Inversión",
        "content": "... HTML de arriba ..."
      }
    }
  }'
```

## Verificación

Después de aplicar las plantillas:
1. Agrega un correo de prueba en /admin/acceso
2. Revisa el correo recibido
3. Verifica que el enlace incluya `token_hash` y `type` en la URL
4. Confirma que el enlace funcione al abrirlo en un navegador diferente
