# from pydantic_settings import BaseSettings, SettingsConfigDict

# class Settings(BaseSettings):
#     api_prefix: str = "/api"
#     DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@catalog-db:5432/catalogo"
#     REDIS_URL: str = "redis://redis:6379/1"
#     page_size_default: int = 20
#     page_size_max: int = 50

#     model_config = SettingsConfigDict(
#         env_file=".env",
#         env_file_encoding="utf-8",
#         case_sensitive=False,
#         extra="ignore"  # Ignorar variables extra del entorno
#     )

# settings = Settings()

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://medisupply_user:MediSupply_Prod_2024!@catalog-db:5432/catalogo"
    REDIS_URL: str = "redis://:Redis_MediSupply_2024!@redis:6379/1"
    api_prefix: str = "/api"
    page_size_default: int = 20
    page_size_max: int = 50

    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
