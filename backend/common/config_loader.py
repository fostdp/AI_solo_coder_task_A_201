import json
import os
from typing import Dict, Any, Tuple, List

_CONFIG_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_CONFIG_DIR = os.path.join(_CONFIG_DIR, "config")


def _load_json(filename: str) -> Dict[str, Any]:
    filepath = os.path.join(_CONFIG_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


_casting_config: Dict[str, Any] = {}
_criteria_config: Dict[str, Any] = {}
_redis_config: Dict[str, Any] = {}


def load_all_configs():
    global _casting_config, _criteria_config, _redis_config
    _casting_config = _load_json("casting_parameters.json")
    _criteria_config = _load_json("criteria_parameters.json")
    _redis_config = _load_json("redis_config.json")


def get_casting_config() -> Dict[str, Any]:
    if not _casting_config:
        load_all_configs()
    return _casting_config


def get_criteria_config() -> Dict[str, Any]:
    if not _criteria_config:
        load_all_configs()
    return _criteria_config


def get_redis_config() -> Dict[str, Any]:
    if not _redis_config:
        load_all_configs()
    return _redis_config


def get_grid_size() -> Tuple[int, int, int]:
    cfg = get_casting_config()
    return tuple(cfg["grid_size"])


def get_total_steps() -> int:
    return get_casting_config()["total_steps"]


def get_default_alloy() -> str:
    return get_casting_config()["default_alloy"]


def get_niyama_threshold(alloy: str | None = None) -> float:
    cfg = get_criteria_config()
    key = alloy or get_default_alloy()
    return cfg["alloy_niyama_thresholds"].get(key, cfg["alloy_niyama_thresholds"][get_default_alloy()])


def get_alloy_name(alloy: str) -> str:
    cfg = get_criteria_config()
    return cfg["alloy_names"].get(alloy, alloy)


def get_all_alloys() -> Dict[str, str]:
    return get_criteria_config()["alloy_names"]


def get_alert_thresholds() -> Dict[str, float]:
    cfg = get_casting_config()
    return cfg["alert_thresholds"]


def get_thermal_properties() -> Dict[str, float]:
    cfg = get_casting_config()
    return cfg["thermal_properties"]


def get_temperature_range() -> Dict[str, float]:
    cfg = get_casting_config()
    return cfg["temperature_range"]


def get_redis_channel(key: str) -> str:
    cfg = get_redis_config()
    return cfg["channels"][key]


def get_redis_connection_params() -> Dict[str, Any]:
    cfg = get_redis_config()
    return {
        "host": cfg["host"],
        "port": cfg["port"],
        "db": cfg["db"],
    }
