# Sistema de Autenticación con Contraseñas - Pendiente de Completar

## ✅ Lo que ya está hecho

### Base de datos
- ✅ Migración `20261012010000_password_auth.sql` creada:
  - Campo `must_change_password` en `profiles`
  - Tabla `invitations` para tracking de invitaciones

### Backend parcial
- ✅ `apps/api/app/auth_utils.py` con utilidades:
  - `generate_temp_password()`: genera contraseñas legibles como "Angel-Tango-47"
  - `is_strong_password()`: valida contraseñas fuertes
  - `generate_secure_token()`: tokens seguros para reset

## 🚧 Lo que falta (requiere integración con Supabase Auth)

### Backend (FastAPI)
1. **Endpoint POST /admin/invite-user**:
   - Recibe: email, role
   - Crea usuario en Supabase Auth con contraseña temporal
   - Guarda invitación en tabla `invitations`
   - Envía correo con: link al sitio, email, contraseña temporal
   - Retorna: success o error

2. **Endpoint POST /admin/resend-invitation**:
   - Recibe: email
   - Re-genera contraseña temporal
   - Actualiza `invitations`
   - Reenvía correo

3. **Endpoint POST /auth/change-password**:
   - Recibe: current_password, new_password
   - Valida con `is_strong_password()`
   - Cambia contraseña en Supabase Auth
   - Desmarca `must_change_password` en profiles
   - Marca invitación como `used_at` si existe

4. **Endpoint POST /auth/forgot-password**:
   - Recibe: email
   - Usa Supabase Auth para enviar reset por correo

5. **Métodos en db.py**:
   ```python
   def create_auth_user(self, email: str, password: str) -> str:
       # Llama a Supabase Admin API para crear usuario
       # POST /auth/v1/admin/users
       
   def change_user_password(self, user_id: str, new_password: str):
       # PATCH /auth/v1/admin/users/{user_id}
       
   def save_invitation(self, email: str, temp_password: str, invited_by: str):
       # INSERT into invitations
       
   def get_invitation(self, email: str) -> dict | None:
       # SELECT from invitations where not used
   ```

### Frontend (Next.js)
1. **Página /login** actualizada:
   - Form con email + password (en lugar de magic link)
   - Link "¿Olvidaste tu contraseña?"
   - Opcional: botón de Google si ya funciona

2. **Página /change-password** (primera vez):
   - Detecta `must_change_password` del user
   - Form: contraseña actual (temporal) + nueva + confirmar
   - No deja usar la app hasta cambiar

3. **Página /forgot-password**:
   - Form simple con email
   - Mensaje "Revisa tu correo"

4. **Actualizar /admin/acceso**:
   - Botón "Invitar" en lugar de "Agregar"
   - Modal/form: email + rol
   - Botón "Reenviar invitación" por usuario
   - Mostrar si tienen invitación pendiente

### Plantilla de correo
Archivo: `apps/api/app/templates/invitation_email.html` (o .txt)
```
Asunto: Invitación a la plataforma de inversión

Hola,

Has sido invitado a la plataforma de inversión.

Entra aquí: {SITE_URL}/login
Tu correo: {email}
Contraseña temporal: {temp_password}

En tu primer inicio de sesión se te pedirá cambiar esta contraseña.

La invitación expira en 7 días.
```

## 🔧 Script para Diego (obtener su contraseña temporal)

Crear `apps/api/scripts/reset_admin_password.py`:
```python
#!/usr/bin/env python
"""Genera contraseña temporal para el admin existente."""
import sys
from app.auth_utils import generate_temp_password
from app.config import get_settings
from app.db import SupabaseRest

def main():
    email = "salinas.diegoarmando03@gmail.com"
    settings = get_settings()
    db = SupabaseRest(settings)
    
    # Generar contraseña temporal
    temp_password = generate_temp_password()
    
    # Guardar en invitations para tracking
    db.execute(
        "INSERT INTO invitations (email, temp_password, invited_by) VALUES (:email, :temp, 'script') ON CONFLICT (email) DO UPDATE SET temp_password = :temp",
        {"email": email, "temp": temp_password}
    )
    
    # Actualizar en Supabase Auth (requiere Admin API)
    # user_id = db.get_user_id_by_email(email)
    # db.change_user_password(user_id, temp_password)
    
    print(f"Contraseña temporal para {email}:")
    print(f"  {temp_password}")
    print("")
    print("IMPORTANTE: Cambia esta contraseña en tu primer login.")
    
    db.close()

if __name__ == "__main__":
    main()
```

Ejecutar: `cd apps/api && uv run python scripts/reset_admin_password.py`

## 📚 Recursos necesarios

- [Supabase Admin API - Create User](https://supabase.com/docs/reference/javascript/auth-admin-createuser)
- [Supabase Admin API - Update User](https://supabase.com/docs/reference/javascript/auth-admin-updateuserbyid)
- Python requests para llamar a `/auth/v1/admin/users` con service_role_key

## ⚠️ Decisión

Este sistema de contraseñas requiere ~6-8 horas adicionales de trabajo enfocado para:
1. Integrar Supabase Admin API correctamente
2. Crear los endpoints backend
3. Actualizar el frontend completo
4. Probar el flujo end-to-end
5. Escribir tests

**Recomendación**: Mergear lo que ya está (automatización + UX + responsive) que aporta valor inmediato, y hacer el sistema de contraseñas en un PR separado cuando tengas tiempo dedicado.

O si prefieres, puedo continuar en una segunda sesión enfocada 100% en completar esto.
