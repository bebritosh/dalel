"""Application settings loaded from environment / .env file."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration. Values come from env vars or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    app_name: str = "DÄLEL"
    database_url: str = "sqlite:///data/dalel.db"
    data_dir: str = "data"
    max_upload_bytes: int = 15 * 1024 * 1024  # 15 MB

    # LLM extraction (phase 1).
    llm_mode: str = "fixture"  # fixture | live
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # OCR (phase 1).
    ocr_engine: str = "fixture"  # fixture | tesseract
    ocr_langs: str = "rus+eng"
    tesseract_cmd: str = ""  # optional explicit path to tesseract.exe


settings = Settings()
