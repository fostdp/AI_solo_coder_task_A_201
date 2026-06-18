from typing import Dict, Any, Optional


class SensorValidator:
    def __init__(self):
        self.ranges = {
            "wax_temperature": (0, 2000),
            "pouring_temperature": (0, 2000),
            "shell_permeability": (0, 100),
            "filling_progress": (0, 100),
        }

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        errors = []

        if "casting_id" not in data or not data["casting_id"]:
            errors.append("casting_id is required")

        for field, (min_val, max_val) in self.ranges.items():
            if field not in data:
                errors.append(f"{field} is missing")
                continue
            value = data[field]
            if not isinstance(value, (int, float)):
                errors.append(f"{field} must be a number")
                continue
            if value < min_val or value > max_val:
                errors.append(f"{field} must be between {min_val} and {max_val}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = {}
        for key in ["casting_id", "wax_temperature", "pouring_temperature", "shell_permeability", "filling_progress"]:
            if key in data:
                normalized[key] = data[key]
        if "timestamp" not in normalized:
            from datetime import datetime
            normalized["timestamp"] = datetime.now()
        return normalized


sensor_validator = SensorValidator()
