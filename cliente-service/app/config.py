from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://cliente_user:cliente_pass@cliente-db:5432/cliente_db"
    REDIS_URL: str = "redis://:redis_password@redis:6379/2"
    api_prefix: str = "/api"
    page_size_default: int = 20
    page_size_max: int = 50
    
    # Campos adicionales del docker-compose
    sla_max_response_ms: int = 2000
    max_historico_items: int = 100
    max_productos_preferidos: int = 20
    max_devoluciones: int = 50
    log_level: str = "INFO"
    log_format: str = "json"
    debug: bool = False
    orders_service_url: str = "http://orders-service:3000"
    catalogo_service_url: str = "http://catalog-service:3001"
    allowed_origins: str = "*"
    allowed_methods: str = "*"
    allowed_headers: str = "*"
    
    # Campos de autenticación (opcionales)
    secret_key: str = "cliente-service-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    health_check_timeout: int = 5

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"  # Ignorar campos extra en lugar de fallar
    }

settings = Settings()

def get_settings() -> Settings:
    """Función para obtener la configuración (patrón singleton)"""
    return settings