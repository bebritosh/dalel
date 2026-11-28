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
    # fixture | live (Anthropic) | openai | rules (rule-based baseline) | auto
    llm_mode: str = "fixture"
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-5-5"
    openai_api_key: str = ""
    openai_model: str = "gpt-5.4-mini"
    # Opt-in: save real LLM responses as eval/fixtures/{sha}.json (offline replay).
    save_llm_fixtures: bool = False

    # OCR (phase 1).
    ocr_engine: str = "fixture"  # fixture | tesseract | auto (LLM_MODE=auto also forces auto OCR)
    ocr_langs: str = "rus+eng"
    tesseract_cmd: str = ""  # optional explicit path to tesseract.exe

    # PDF export (phase 7): path to LibreOffice's soffice binary. Empty => auto
    # detect (PATH + standard install locations); if still missing, PDF -> 503.
    soffice_path: str = ""


settings = Settings()
