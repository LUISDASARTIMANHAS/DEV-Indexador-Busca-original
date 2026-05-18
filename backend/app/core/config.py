from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_env_file() -> Path | None:
    current = Path(__file__).resolve()
    for parent in current.parents:
        candidate = parent / ".env"
        if candidate.exists():
            return candidate
    return None


ENV_FILE = _find_env_file()
if ENV_FILE is not None:
    load_dotenv(ENV_FILE)


class Settings(BaseSettings):
    # ── Variáveis separadas ───────────────────────────────
    DATABASE_USER: str = "admin"
    DATABASE_PASSWORD: str = "admin"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "ifesdoc"

    # ── URL final (opcional override via .env) ────────────
    DATABASE_URL: str | None = None

    # ── Outras configs ────────────────────────────────────
    SECRET_KEY: str = "super-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    SESSION_IDLE_EXPIRE_MINUTES: int = 30

    DOCUMENT_UPLOAD_DIR: str = "backend/storage/documents"
    DOCUMENT_MAX_FILE_SIZE_MB: int = 50
    DOCUMENT_ALLOWED_EXTENSIONS: list[str] = ["pdf", "docx", "txt", "csv"]

    NOTIFICATION_WORKER_INTERVAL_SECONDS: int = 60

    BACKEND_CORS_ORIGINS: list[str] = [
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    model_config = SettingsConfigDict(
        env_file=ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_database_url(self) -> str:
        """
        Monta automaticamente a DATABASE_URL se não existir.

        @return str: URL do banco pronta para SQLAlchemy
        """
        if self.DATABASE_URL:
            # Corrige caso venha errado
            if self.DATABASE_URL.startswith("postgres://"):
                return self.DATABASE_URL.replace("postgres://", "postgresql://")
            return self.DATABASE_URL

        password = quote_plus(self.DATABASE_PASSWORD)

        return (
            f"postgresql://{self.DATABASE_USER}:{password}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


settings = Settings()
