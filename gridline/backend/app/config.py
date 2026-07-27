"""Application configuration.

All settings are environment driven so the same image runs in dev, staging and
production. Nothing here should have a production-unsafe default that silently
enables a destructive or costly behaviour.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- Service identity -------------------------------------------------
    app_name: str = "GridLine AI"
    app_version: str = "1.0.0"
    environment: str = Field(default="development")
    debug: bool = Field(default=False)

    # --- HTTP -------------------------------------------------------------
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    max_upload_bytes: int = Field(default=15 * 1024 * 1024)  # 15 MB

    # --- Database ---------------------------------------------------------
    database_url: str = Field(
        default="postgresql+asyncpg://gridline:gridline@localhost:5432/gridline"
    )
    db_pool_size: int = 10
    db_max_overflow: int = 20
    db_echo: bool = False

    # --- Object storage (S3 compatible: AWS S3, MinIO, R2, ...) -----------
    s3_endpoint_url: str | None = Field(default=None)
    s3_region: str = Field(default="us-east-1")
    s3_bucket: str = Field(default="gridline-inspections")
    s3_access_key_id: str | None = None
    s3_secret_access_key: str | None = None
    s3_public_base_url: str | None = None
    s3_force_path_style: bool = True
    # When no S3 credentials are configured we fall back to the local disk so
    # a developer can run the whole stack with docker compose alone.
    local_storage_dir: str = "./.storage"

    # --- Vision model -----------------------------------------------------
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    vision_model: str = "gpt-4o"
    vision_timeout_seconds: float = 60.0
    vision_max_retries: int = 2
    # Set false to run entirely on the deterministic fallback analyzer (useful
    # for CI, offline demos and cost control).
    vision_enabled: bool = True

    # --- GIS --------------------------------------------------------------
    overpass_url: str = "https://overpass-api.de/api/interpreter"
    overpass_timeout_seconds: float = 45.0
    overpass_user_agent: str = "GridLineAI/1.0 (infrastructure inspection; +https://chargebotic.com)"
    gis_default_radius_m: int = 400
    gis_max_radius_m: int = 5000
    gis_cache_ttl_seconds: int = 24 * 3600
    usgs_hifld_transmission_url: str | None = Field(
        default="https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Transmission_Lines/FeatureServer/0/query"
    )
    usgs_hifld_substation_url: str | None = Field(
        default="https://services1.arcgis.com/Hp6G80Pky0om7QvQ/arcgis/rest/services/Electric_Substations/FeatureServer/0/query"
    )
    external_gis_enabled: bool = True

    # --- Security ---------------------------------------------------------
    admin_api_key: str | None = None
    rate_limit_analyze_per_minute: int = 20

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def storage_is_s3(self) -> bool:
        return bool(self.s3_access_key_id and self.s3_secret_access_key)

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
