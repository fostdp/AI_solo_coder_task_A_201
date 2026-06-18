import numpy as np
import uuid
from datetime import datetime
from typing import List, Dict, Tuple
from config import settings

class DefectPredictionService:
    def __init__(self, grid_size: Tuple[int, int, int] = (20, 20, 20)):
        self.grid_size = grid_size
        self.niyama_field = np.zeros(grid_size, dtype=np.float32)
        self.detected_defects: List[Dict] = []

    def reset(self):
        self.niyama_field = np.zeros(self.grid_size, dtype=np.float32)
        self.detected_defects = []

    def calculate_niyama(
        self,
        temperature_field: np.ndarray,
        temperature_gradient: np.ndarray,
        cooling_rate: np.ndarray,
    ) -> Dict:
        gx, gy, gz = self.grid_size
        grad_magnitude = np.linalg.norm(temperature_gradient, axis=-1)
        safe_cooling = np.maximum(cooling_rate, 1e-6)
        self.niyama_field = grad_magnitude / np.sqrt(safe_cooling)

        points = []
        for x in range(0, gx, 2):
            for y in range(0, gy, 2):
                for z in range(0, gz, 2):
                    points.append({
                        "x": float(x) / gx,
                        "y": float(y) / gy,
                        "z": float(z) / gz,
                        "niyama": float(self.niyama_field[x, y, z]),
                    })

        return {
            "niyama_field": self.niyama_field.tolist(),
            "points": points,
            "mean_niyama": float(np.mean(self.niyama_field)),
            "min_niyama": float(np.min(self.niyama_field)),
            "max_niyama": float(np.max(self.niyama_field)),
        }

    def predict_defects(
        self,
        casting_id: str,
        temperature_field: np.ndarray,
        niyama_threshold: float = None,
    ) -> List[Dict]:
        if niyama_threshold is None:
            niyama_threshold = settings.NIYAMA_THRESHOLD

        gx, gy, gz = self.grid_size
        self.detected_defects = []
        visited = np.zeros((gx, gy, gz), dtype=bool)

        for x in range(gx):
            for y in range(gy):
                for z in range(gz):
                    if not visited[x, y, z] and self.niyama_field[x, y, z] < niyama_threshold:
                        cluster = self._flood_fill(x, y, z, visited, niyama_threshold)
                        if len(cluster) >= 3:
                            volume = len(cluster) * 0.5
                            cx = np.mean([p[0] for p in cluster]) / gx
                            cy = np.mean([p[1] for p in cluster]) / gy
                            cz = np.mean([p[2] for p in cluster]) / gz
                            mean_niyama = np.mean([self.niyama_field[p[0], p[1], p[2]] for p in cluster])
                            mean_temp = np.mean([temperature_field[p[0], p[1], p[2]] for p in cluster])

                            if volume < 1.0:
                                severity = "low"
                                defect_type = "shrinkage_porosity"
                            elif volume < 3.0:
                                severity = "medium"
                                defect_type = "shrinkage_porosity"
                            elif volume < 5.0:
                                severity = "high"
                                defect_type = "shrinkage_cavity"
                            else:
                                severity = "critical"
                                defect_type = "shrinkage_cavity"

                            self.detected_defects.append({
                                "id": str(uuid.uuid4()),
                                "casting_id": casting_id,
                                "position": {"x": float(cx), "y": float(cy), "z": float(cz)},
                                "niyama_value": float(mean_niyama),
                                "volume": float(volume),
                                "severity": severity,
                                "defect_type": defect_type,
                                "mean_temperature": float(mean_temp),
                                "detected_at": datetime.now(),
                            })

        return self.detected_defects

    def _flood_fill(
        self, x: int, y: int, z: int, visited: np.ndarray, threshold: float
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
            if self.niyama_field[cx, cy, cz] >= threshold:
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
