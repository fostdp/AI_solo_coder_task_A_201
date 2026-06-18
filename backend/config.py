from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "lost_wax_casting"
    SENSOR_INTERVAL: int = 60
    NIYAMA_THRESHOLD: float = 1.0
    MAX_SHRINKAGE_VOLUME: float = 5.0
    MIN_FILLING_RATIO: float = 0.95
    ALERT_WS_PORT: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
