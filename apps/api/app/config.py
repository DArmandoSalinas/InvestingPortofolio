import os
from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

API_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = Path(__file__).resolve().parents[3]
KEY_NAMES = ("XAI_API_KEY", "GrokAI")


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    supabase_anon_key: str
    admin_email: str
    rank_highlight_min: int = 70
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[1] / ".env",
        extra="ignore",
    )

    @field_validator("admin_email")
    @classmethod
    def lowercase_admin(cls, value: str) -> str:
        email = value.strip().lower()
        if "@" not in email:
            raise ValueError("ADMIN_EMAIL tiene que ser un correo")
        return email

    @field_validator("rank_highlight_min")
    @classmethod
    def threshold_range(cls, value: int) -> int:
        if not 0 <= value <= 100:
            raise ValueError("RANK_HIGHLIGHT_MIN tiene que estar entre 0 y 100")
        return value

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def vapid_public_key(self) -> str:
        return env_value("VAPID_PUBLIC_KEY")

    @property
    def vapid_private_key(self) -> str:
        return env_value("VAPID_PRIVATE_KEY")

    @property
    def vapid_subject(self) -> str:
        return env_value("VAPID_SUBJECT") or "mailto:admin@estudio.local"

    @property
    def site_url(self) -> str:
        return env_value("SITE_URL") or "http://localhost:3000"

    @property
    def xai_api_key(self) -> str:
        for name in KEY_NAMES:
            found = os.environ.get(name, "").strip().strip('"').strip("'")
            if found:
                return found
        for path in (API_DIR / ".env", ROOT_DIR / ".env"):
            found = _key_in_file(path)
            if found:
                return found
        return ""


def env_value(name: str) -> str:
    found = os.environ.get(name, "").strip().strip('"').strip("'")
    if found:
        return found
    for path in (API_DIR / ".env", ROOT_DIR / ".env"):
        found = _named_in_file(path, {name})
        if found:
            return found
    return ""


def _key_in_file(path: Path) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        name, value = text.split("=", 1)
        if name.strip() in KEY_NAMES:
            return value.strip().strip('"').strip("'")
    return ""


def _named_in_file(path: Path, names: set[str]) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text().splitlines():
        text = line.strip()
        if not text or text.startswith("#") or "=" not in text:
            continue
        name, value = text.split("=", 1)
        if name.strip() in names:
            return value.strip().strip('"').strip("'")
    return ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
