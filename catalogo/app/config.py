from pydantic import BaseModel
import os

class Settings(BaseModel):
    api_prefix: str = os.getenv("API_PREFIX", "/api")
    db_url: str = os.getenv("DB_URL")
    redis_url: str = os.getenv("REDIS_URL")
    page_size_default: int = int(os.getenv("PAGE_SIZE_DEFAULT", "20"))
    page_size_max: int = int(os.getenv("PAGE_SIZE_MAX", "50"))

settings = Settings()
