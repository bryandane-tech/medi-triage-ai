from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "MediTriage Enterprise"
    DATABASE_URL: str = "postgresql://postgres:postgrespassword@localhost:5432/meditriage"
    REDIS_URL: str = "redis://localhost:6379"
    MASTER_KEY_B64: str = "c3VwZXJzZWNyZXRtYXN0ZXJrZXkzMmJ5dGVzbG9uZw=="
    C_LIB_PATH: str = "/app/c_engine/libtriage.so"
    DB_MIN_POOL: int = 5
    DB_MAX_POOL: int = 20

    class Config:
        env_file = ".env"

settings = Settings()
