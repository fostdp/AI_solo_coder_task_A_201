import numpy as np
import uuid
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from config import settings, ALLOY_NAMES

BRONZE_VOLUME_SCALE = 0.42
THRESHOLD_BRONZE_LOW = 0.58
THRESHOLD_BRONZE_MEDIUM = 0.42
THRESHOLD_BRONZE_HIGH = 0.30
THRESHOLD_BRONZE_CRITICAL = 0.18

class DefectPredictionService:
    def __init__(self, grid_size: Tuple[int, int, int] = (20, 20, 20), alloy: str = "zeng_houyi_bronze"):
        self.grid_size = grid_size
        self.alloy = alloy
        self.niyama_threshold = settings.get_niyama_threshold(alloy)
        self.alloy_name = ALLOY_NAMES.get(alloy, alloy)
        self.niyama_field = np.zeros(grid_size, dtype=np.float32)
        self.detected_defects: List[Dict] = []
        self.local_threshold_field: Optional[np.ndarray] = None

    def reset(self):
        self.niyama_field = np.zeros(self.grid_size, dtype=np.float32)
        self.detected_defects = []
        self.local_threshold_field = None

    def set_alloy(self, alloy: str):
        self.alloy = alloy
        self.niyama_threshold = settings.get_niyama_threshold(alloy)
        self.alloy_name = ALLOY_NAMES.get(alloy, alloy)

    def calculate_niyama(
        self,
        temperature_field: np.ndarray,
        temperature_gradient: np.ndarray,
        cooling_rate: np.ndarray,
        solidus_temp: float = 950.0,
        liquidus_temp: float = 1083.0,
    ) -> Dict:
        gx, gy, gz = self.grid_size
        grad_magnitude = np.linalg.norm(temperature_gradient, axis=-1)
        safe_cooling = np.maximum(cooling_rate, 1e-6)
        base_niyama = grad_magnitude / np.sqrt(safe_cooling)

        if self.alloy in ("bronze", "zeng_houyi_bronze", "brass", "copper"):
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
            for x in range(gx_):
                for y in range(gy_):
                    for z in range(gz_):
                        tn = temp_norm[x, y, z] if temperature_field[x, y, z] < liquidus else 1.0
                        thickness_penalty = 1.0
                        dx = min(x, gx_ - 1 - x)
                        dy = min(y, gy_ - 1 - y)
                        if min(dx, dy) <= 1:
                            thickness_penalty = 1.25
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

    def predict_defects(
        self,
        casting_id: str,
        temperature_field: np.ndarray,
        niyama_threshold: float | None = None,
    ) -> List[Dict]:
        if niyama_threshold is None:
            niyama_threshold = self.niyama_threshold

        gx, gy, gz = self.grid_size
        self.detected_defects = []
        visited = np.zeros((gx, gy, gz), dtype=bool)

        threshold_field = (
            self.local_threshold_field
            if self.local_threshold_field is not None
            else np.full((gx, gy, gz), niyama_threshold, dtype=np.float32)
        )

        is_bronze_alloy = self.alloy in ("bronze", "zeng_houyi_bronze", "brass", "copper")

        for x in range(gx):
            for y in range(gy):
                for z in range(gz):
                    th = float(threshold_field[x, y, z])
                    if not visited[x, y, z] and self.niyama_field[x, y, z] < th:
                        cluster = self._flood_fill(x, y, z, visited, th, threshold_field)
                        if len(cluster) >= 3:
                            volume = len(cluster) * (BRONZE_VOLUME_SCALE if is_bronze_alloy else 0.5)
                            cx = np.mean([p[0] for p in cluster]) / gx
                            cy = np.mean([p[1] for p in cluster]) / gy
                            cz = np.mean([p[2] for p in cluster]) / gz
                            mean_niyama = np.mean([self.niyama_field[p[0], p[1], p[2]] for p in cluster])
                            mean_temp = np.mean([temperature_field[p[0], p[1], p[2]] for p in cluster])

                            if is_bronze_alloy:
                                if volume < 0.8:
                                    severity = "low"
                                elif volume < 2.2:
                                    severity = "medium"
                                elif volume < 4.0:
                                    severity = "high"
                                else:
                                    severity = "critical"
                            else:
                                if volume < 1.0:
                                    severity = "low"
                                elif volume < 3.0:
                                    severity = "medium"
                                elif volume < 5.0:
                                    severity = "high"
                                else:
                                    severity = "critical"

                            defect_type = (
                                "shrinkage_cavity" if volume > (2.5 if is_bronze_alloy else 3.0) else "shrinkage_porosity"
                            )

                            self.detected_defects.append({
                                "id": str(uuid.uuid4()),
                                "casting_id": casting_id,
                                "position": {"x": float(cx), "y": float(cy), "z": float(cz)},
                                "niyama_value": float(mean_niyama),
                                "niyama_threshold": float(np.mean([threshold_field[p[0], p[1], p[2]] for p in cluster])),
                                "volume": float(volume),
                                "severity": severity,
                                "defect_type": defect_type,
                                "mean_temperature": float(mean_temp),
                                "alloy": self.alloy,
                                "alloy_name": self.alloy_name,
                                "detected_at": datetime.now(),
                            })

        return self.detected_defects

    def _flood_fill(
        self,
        x: int, y: int, z: int,
        visited: np.ndarray,
        threshold: float,
        threshold_field: np.ndarray | None = None,
    ) -> List[Tuple[int, int, int]]:
        gx, gy, gz = self.grid_size
        stack = [(x, y, z)]
        cluster = []
        while stack:
            cx, cy, cz = stack.pop()
            if cx < 0 or cx >= gx or cy < 0 or cy >= gy or cz < 0 or cz >= gz:
                continue
            if visited[cx, cy, cz]:
                continue
            th = float(threshold_field[cx, cy, cz]) if threshold_field is not None else threshold
            if self.niyama_field[cx, cy, cz] >= th:
                continue
            visited[cx, cy, cz] = True
            cluster.append((cx, cy, cz))
            stack.extend([
                (cx + 1, cy, cz), (cx - 1, cy, cz),
                (cx, cy + 1, cz), (cx, cy - 1, cz),
                (cx, cy, cz + 1), (cx, cy, cz - 1),
            ])
        return cluster

    def get_critical_defects(self) -> List[Dict]:
        return [d for d in self.detected_defects if d["severity"] in ["high", "critical"]]

    def get_total_shrinkage_volume(self) -> float:
        return sum(d["volume"] for d in self.detected_defects)
