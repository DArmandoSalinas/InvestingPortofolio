"""Utilidades para autenticación con contraseñas."""
import random
import secrets
import string


# Palabras simples y legibles para contraseñas temporales
WORDS = [
    "angel", "bravo", "carta", "delta", "echo", "faro", "golf", "hotel",
    "india", "julio", "kilo", "lima", "metro", "norte", "opera", "papa",
    "queso", "romeo", "sierra", "tango", "union", "victor", "whisky", "xray",
    "yankee", "zulu", "alto", "bajo", "casa", "dedo", "este", "foca",
]


def generate_temp_password() -> str:
    """
    Genera una contraseña temporal legible y fácil de escribir.
    Formato: Palabra-Palabra-Numero (ej: Angel-Tango-47)
    """
    word1 = random.choice(WORDS).capitalize()
    word2 = random.choice(WORDS).capitalize()
    number = random.randint(10, 99)
    return f"{word1}-{word2}-{number}"


def generate_secure_token(length: int = 32) -> str:
    """Genera un token seguro para reset de contraseña."""
    return secrets.token_urlsafe(length)


def is_strong_password(password: str) -> tuple[bool, str]:
    """
    Valida que una contraseña sea suficientemente fuerte.
    Retorna (es_valida, mensaje_error).
    """
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    
    if not (has_upper and has_lower and has_digit):
        return False, "La contraseña debe tener mayúsculas, minúsculas y números"
    
    return True, ""
