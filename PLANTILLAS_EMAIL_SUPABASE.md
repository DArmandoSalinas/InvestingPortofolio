# Plantillas de correo de Supabase para password reset

Para que el flujo de restablecimiento de contraseña funcione en cualquier navegador (incluso si se abre el enlace en Gmail app u otro navegador), debes actualizar la plantilla de correo de **Reset password** en Supabase (Authentication → Email Templates).

## Reset password (Restablecer contraseña)

**Cuándo se usa:** Cuando un usuario hace clic en "Olvidé mi contraseña" en `/olvidar`

**Asunto:** Restablece tu contraseña de Inversión

**Contenido HTML:**
```html
<div style="font-family: system-ui, -apple-system, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
  <h2 style="color: #f5f5f7; margin-bottom: 16px;">Restablece tu contraseña</h2>

  <p style="color: #8e8e93; line-height: 1.6; margin-bottom: 20px;">
    Recibimos una solicitud para restablecer la contraseña de tu cuenta en Inversión.
  </p>

  <p style="color: #8e8e93; line-height: 1.6; margin-bottom: 24px;">
    Haz clic en el siguiente enlace para crear una nueva contraseña:
  </p>

  <div style="margin: 32px 0;">
    <a href="{{ .SiteURL }}/auth/confirm?token_hash={{ .TokenHash }}&type=recovery&next=/cambiar-contrasena" 
       style="display: inline-block; background-color: #f5f5f7; color: #000; padding: 12px 24px; border-radius: 24px; text-decoration: none; font-weight: 500;">
      Restablecer mi contraseña
    </a>
  </div>

  <p style="color: #636366; font-size: 14px; line-height: 1.6; margin-top: 32px;">
    Este enlace caduca en 1 hora.
  </p>

  <p style="color: #636366; font-size: 14px; line-height: 1.6;">
    Si no solicitaste restablecer tu contraseña, ignora este mensaje.
  </p>

  <hr style="border: none; border-top: 1px solid #2a2a2a; margin: 32px 0;" />

  <p style="color: #636366; font-size: 12px;">
    Inversión – Plataforma privada de análisis. El contenido es informativo, no es asesoría financiera.
  </p>
</div>
```

## Nota importante sobre {{ .TokenHash }}

El cambio clave es usar `{{ .TokenHash }}` en lugar de `{{ .Token }}` o `{{ .ConfirmationURL }}`. 

**Por qué:**
- El flujo con `token_hash` funciona en cualquier navegador, incluso si el usuario abre el enlace en un navegador diferente o en la app de Gmail
- El flujo PKCE anterior con `code` fallaba si se abría en un contexto diferente
- La ruta `/auth/confirm` con `type=recovery` usa `verifyOtp` que maneja correctamente el `token_hash`

**Parámetros del enlace:**
- `token_hash={{ .TokenHash }}`: Token seguro que funciona cross-browser
- `type=recovery`: Indica que es un flujo de recuperación de contraseña
- `next=/cambiar-contrasena`: Redirige a la página para establecer nueva contraseña

## Aplicar la plantilla

### Opción A: Manual en el Dashboard de Supabase
1. Ve a tu proyecto en https://supabase.com/dashboard
2. Authentication → Email Templates
3. Selecciona "Reset password"
4. Pega el HTML de arriba
5. Guarda los cambios

### Opción B: Management API (automatizado)
```bash
# Requiere tu Management API token de Supabase
curl -X PATCH \
  https://api.supabase.com/v1/projects/{project-ref}/config/auth \
  -H "Authorization: Bearer {management-token}" \
  -H "Content-Type: application/json" \
  -d '{
    "MAILER_TEMPLATES": {
      "recovery": {
        "subject": "Restablece tu contraseña de Inversión",
        "content": "... HTML de arriba ..."
      }
    }
  }'
```

## Verificación

Después de aplicar la plantilla:
1. Ve a `/olvidar` e ingresa un correo registrado
2. Revisa el correo recibido
3. Verifica que el enlace incluya `token_hash`, `type=recovery` y `next=/cambiar-contrasena`
4. Confirma que el enlace funcione al abrirlo en un navegador diferente
5. Verifica que te lleve a `/cambiar-contrasena` para establecer nueva contraseña

## Variables de entorno para envío de correos

### Railway (recomendado)
Railway bloquea SMTP saliente en el plan gratuito. Usa Brevo (SendinBlue) API HTTP:

```bash
BREVO_API_KEY=xkeysib-...           # Llave de API de Brevo
BREVO_SENDER_EMAIL=noreply@tu-dominio.com  # (opcional, default: noreply@inversion.app)
BREVO_SENDER_NAME=Inversión         # (opcional, default: Inversión)
```

### SMTP (alternativa)
Si tienes un servidor SMTP disponible:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=tu-correo@gmail.com
SMTP_PASSWORD=tu-app-password
SMTP_FROM=noreply@tu-dominio.com
```

**Prioridad de envío:**
1. Brevo (si `BREVO_API_KEY` existe)
2. SMTP (si `SMTP_HOST` y `SMTP_FROM` existen)
3. Mailpit local (desarrollo)
