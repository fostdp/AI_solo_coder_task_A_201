import numpy as np
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from common.config_loader import (
    get_grid_size,
    get_default_alloy,
    get_niyama_threshold,
    get_alloy_name,
    get_criteria_config,
    get_temperature_range,
)


class NiyamaCalculator:
    def __init__(self, grid_size: Tuple[int, int, int] | None = None, alloy: str | None = None):
        self.grid_size = grid_size or get_grid_size()
        self.alloy = alloy or get_default_alloy()
        self.niyama_threshold = get_niyama_threshold(self.alloy)
        self.alloy_name = get_alloy_name(self.alloy)
        self.niyama_field = np.zeros(self.grid_size, dtype=np.float32)
        self.local_threshold_field: Optional[np.ndarray] = None
        self._criteria_config = get_criteria_config()

    def reset(self):
        self.niyama_field = np.zeros(self.grid_size, dtype=np.float32)
        self.local_threshold_field = None

    def set_alloy(self, alloy: str):
        self.alloy = alloy
        self.niyama_threshold = get_niyama_threshold(alloy)
        self.alloy_name = get_alloy_name(alloy)

    def calculate(
        self,
        temperature_field: np.ndarray,
        temperature_gradient: np.ndarray,
        cooling_rate: np.ndarray,
    ) -> Dict:
        temp_range = get_temperature_range()
        solidus_temp = temp_range["solidus"]
        liquidus_temp = temp_range["liquidus"]
        gx, gy, gz = self.grid_size
        grad_magnitude = np.linalg.norm(temperature_gradient, axis=-1)
        safe_cooling = np.maximum(cooling_rate, 1e-6)
        base_niyama = grad_magnitude / np.sqrt(safe_cooling)

        bronze_alloys = ("bronze", "zeng_houyi_bronze", "brass", "copper")
        if self.alloy in bronze_alloys:
            solidus, liquidus = solidus_temp, liquidus_temp
            trange = max(1.0, liquidus - solidus)
            temp_norm = np.clip((temperature_field - solidus) / trange, 0.0, 1.0)
            mushy_factor = 0.6 + 0.4 * np.exp(-3.0 * temp_norm)
            phase_factor = np.where(
                temperature_field < solidus,
                1.0,
                np.where(
                    temperature_field > liquidus,
                    0.8,
                    mushy_factor,
                ),
            )
            self.niyama_field = base_niyama * phase_factor

            gx_, gy_, gz_ = self.grid_size
            self.local_threshold_field = np.full(self.grid_size, self.niyama_threshold, dtype=np.float32)
            thickness_penalty_factor = self._criteria_config["defect_clustering"]["thickness_penalty_factor"]
            for x in range(gx_):
                for y in range(gy_):
                    for z in range(gz_):
                        tn = temp_norm[x, y, z] if temperature_field[x, y, z] < liquidus else 1.0
                        thickness_penalty = 1.0
                        dx = min(x, gx_ - 1 - x)
                        dy = min(y, gy_ - 1 - y)
                        if min(dx, dy) <= 1:
                            thickness_penalty = thickness_penalty_factor
                        self.local_threshold_field[x, y, z] = (
                            self.niyama_threshold * (0.8 + 0.4 * tn) * thickness_penalty
                        )
        else:
            self.niyama_field = base_niyama

        points = []
        for x in range(0, gx, 2):
            for y in range(0, gy, 2):
                for z in range(0, gz, 2):
                    local_th = (
                        float(self.local_threshold_field[x, y, z])
                        if self.local_threshold_field is not None
                        else self.niyama_threshold
                    )
                    points.append({
                        "x": float(x) / gx,
                        "y": float(y) / gy,
                        "z": float(z) / gz,
                        "niyama": float(self.niyama_field[x, y, z]),
                        "threshold": local_th,
                    })

        return {
            "niyama_field": self.niyama_field.tolist(),
            "threshold_field": self.local_threshold_field.tolist() if self.local_threshold_field is not None else None,
            "points": points,
            "mean_niyama": float(np.mean(self.niyama_field)),
            "min_niyama": float(np.min(self.niyama_field)),
            "max_niyama": float(np.max(self.niyama_field)),
            "alloy": self.alloy,
            "alloy_name": self.alloy_name,
            "nominal_threshold": self.niyama_threshold,
        }
