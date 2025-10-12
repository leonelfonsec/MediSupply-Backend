from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Local por defecto (docker-compose)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@db:5432/orders"

    # Redis solo si lo usas (local). En ECS probablemente no lo tendrás aún.
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/0"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Garantiza que sea async incluso si el Secret trae 'postgresql://'."""
        url = self.DATABASE_URL
        if url.startswith("postgresql://"):
            url = "postgresql+asyncpg://" + url[len("postgresql://"):]
        return url

settings = Settings()
