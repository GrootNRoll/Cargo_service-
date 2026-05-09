from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./warehouse.db"
    api_prefix: str = "/api"
    seed_demo_data: bool = Field(
        default=False,
        description="При true — один раз заполнить БД демо-данными, если товаров ещё нет",
    )
    cors_origins: str = Field(
        default=(
            "http://localhost:5173,"
            "http://127.0.0.1:5173,"
            "http://localhost:8080,"
            "http://127.0.0.1:8080"
        )
    )

    jwt_secret_key: str = Field(
        default="dev-only-secret-change-in-production",
        description="Секрет подписи JWT",
        validation_alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 12

    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
