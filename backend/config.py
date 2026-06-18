from pydantic_settings import BaseSettings
from typing import Dict


ALLOY_NIYAMA_THRESHOLDS: Dict[str, float] = {
    "steel": 1.0,
    "cast_iron": 0.8,
    "aluminum": 0.45,
    "bronze": 0.6,
    "brass": 0.55,
    "copper": 0.5,
    "zeng_houyi_bronze": 0.58,
}

ALLOY_NAMES: Dict[str, str] = {
    "steel": "钢铁",
    "cast_iron": "铸铁",
    "aluminum": "铝合金",
    "bronze": "青铜 (Cu-Sn)",
    "brass": "黄铜 (Cu-Zn)",
    "copper": "纯铜",
    "zeng_houyi_bronze": "曾侯乙青铜 (Cu-Sn12-Pb2)",
}


class Settings(BaseSettings):
    MONGODB_URL: str = "mongodb://localhost:27017"
    DATABASE_NAME: str = "lost_wax_casting"
    SENSOR_INTERVAL: int = 60
    DEFAULT_ALLOY: str = "zeng_houyi_bronze"
    NIYAMA_THRESHOLD: float = ALLOY_NIYAMA_THRESHOLDS["zeng_houyi_bronze"]
    ALLOY_NIYAMA: Dict[str, float] = ALLOY_NIYAMA_THRESHOLDS
    MAX_SHRINKAGE_VOLUME: float = 5.0
    MIN_FILLING_RATIO: float = 0.95
    ALERT_WS_PORT: int = 8000

    def get_niyama_threshold(self, alloy: str | None = None) -> float:
        key = alloy or self.DEFAULT_ALLOY
        return self.ALLOY_NIYAMA.get(key, self.NIYAMA_THRESHOLD)

    class Config:
        env_file = ".env"


settings = Settings()
