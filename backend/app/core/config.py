from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    app_name: str = "AuditPilot Local"
    api_v1_prefix: str = "/api/v1"
    database_url: str = "sqlite:///./backend/data/auditpilot.db"
    redis_url: str = "redis://127.0.0.1:6379/0"
    sql_echo: bool = False
    default_user_id: str = "00000000-0000-0000-0000-000000000001"
    report_history_limit: int = 200
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )
    storage_root: Path = BACKEND_DIR / "data"

    @property
    def upload_root(self) -> Path:
        return self.storage_root / "uploads"

    @property
    def project_root(self) -> Path:
        return self.storage_root / "projects"

    @property
    def report_root(self) -> Path:
        return self.storage_root / "reports"

    @property
    def template_root(self) -> Path:
        return BACKEND_DIR / "app" / "templates"

    def ensure_directories(self) -> None:
        for path in (
            self.storage_root,
            self.upload_root,
            self.project_root,
            self.report_root,
            self.template_root,
        ):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()

