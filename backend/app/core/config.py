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
    llm_enabled: bool = True
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_reasoning_effort: str = "high"
    deepseek_thinking_enabled: bool = True
    llm_timeout_seconds: int = 60
    llm_max_output_tokens: int = 4096
    llm_max_review_files: int = 6
    llm_max_file_chars: int = 6000
    llm_max_findings: int = 8
    llm_context_index_max_files: int = 160
    llm_context_reference_limit: int = 3
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
    def vulnerability_library_root(self) -> Path:
        return self.storage_root / "vulnerability_library"

    @property
    def default_vulnerability_library_path(self) -> Path:
        return self.vulnerability_library_root / "default.json"

    @property
    def custom_vulnerability_library_root(self) -> Path:
        return self.vulnerability_library_root / "custom"

    @property
    def template_root(self) -> Path:
        return BACKEND_DIR / "app" / "templates"

    def ensure_directories(self) -> None:
        for path in (
            self.storage_root,
            self.upload_root,
            self.project_root,
            self.report_root,
            self.vulnerability_library_root,
            self.custom_vulnerability_library_root,
            self.template_root,
        ):
            path.mkdir(parents=True, exist_ok=True)


settings = Settings()
