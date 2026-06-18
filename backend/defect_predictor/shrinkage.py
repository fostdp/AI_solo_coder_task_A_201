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
)
from .niyama import NiyamaCalculator


class ShrinkageAnalyzer:
    def __init__(self, grid_size: Tuple[int, int, int] | None = None, alloy: str | None = None):
        self.grid_size = grid_size or get_grid_size()
        self.alloy = alloy or get_default_alloy()
        self.niyama_calc = NiyamaCalculator(self.grid_size, self.alloy)
        self.detected_defects: List[Dict] = []
        self._criteria_config = get_criteria_config()

    def reset(self):
        self.niyama_calc.reset()
        self.detected_defects = []

    def set_alloy(self, alloy: str):
        self.alloy = alloy
        self.niyama_calc.set_alloy(alloy)

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
            if self.niyama_calc.niyama_field[cx, cy, cz] >= th:
                continue
            visited[cx, cy, cz] = True
            cluster.append((cx, cy, cz))
            stack.extend([
                (cx + 1, cy, cz), (cx - 1, cy, cz),
                (cx, cy + 1, cz), (cx, cy - 1, cz),
                (cx, cy, cz + 1), (cx, cy, cz - 1),
            ])
        return cluster

    def _classify_severity(self, volume: float, is_bronze: bool) -> str:
        if is_bronze:
            cfg = self._criteria_config["bronze_specific"]["severity_volumes"]
        else:
            cfg = self._criteria_config["general_alloy"]["severity_volumes"]

        if volume < cfg["low"]:
            return "low"
        elif volume < cfg["medium"]:
            return "medium"
        elif volume < cfg["high"]:
            return "high"
        else:
            return "critical"

    def _classify_defect_type(self, volume: float, is_bronze: bool) -> str:
        if is_bronze:
            threshold = self._criteria_config["bronze_specific"]["defect_type_threshold"]
        else:
            threshold = self._criteria_config["general_alloy"]["defect_type_threshold"]
        return "shrinkage_cavity" if volume > threshold else "shrinkage_porosity"

    def predict(
        self,
        casting_id: str,
        temperature_field: np.ndarray,
        temperature_gradient: np.ndarray,
        cooling_rate: np.ndarray,
        niyama_threshold: float | None = None,
    ) -> List[Dict]:
        if niyama_threshold is None:
            niyama_threshold = self.niyama_calc.niyama_threshold

        self.niyama_calc.calculate(temperature_field, temperature_gradient, cooling_rate)

        gx, gy, gz = self.grid_size
        self.detected_defects = []
        visited = np.zeros((gx, gy, gz), dtype=bool)

        threshold_field = (
            self.niyama_calc.local_threshold_field
            if self.niyama_calc.local_threshold_field is not None
            else np.full((gx, gy, gz), niyama_threshold, dtype=np.float32)
        )

        bronze_alloys = ("bronze", "zeng_houyi_bronze", "brass", "copper")
        is_bronze_alloy = self.alloy in bronze_alloys

        if is_bronze_alloy:
            volume_scale = self._criteria_config["bronze_specific"]["volume_scale"]
        else:
            volume_scale = self._criteria_config["general_alloy"]["volume_scale"]

        min_cluster_size = self._criteria_config["defect_clustering"]["min_cluster_size"]

        for x in range(gx):
            for y in range(gy):
                for z in range(gz):
                    th = float(threshold_field[x, y, z])
                    if not visited[x, y, z] and self.niyama_calc.niyama_field[x, y, z] < th:
                        cluster = self._flood_fill(x, y, z, visited, th, threshold_field)
                        if len(cluster) >= min_cluster_size:
                            volume = len(cluster) * volume_scale
                            cx = np.mean([p[0] for p in cluster]) / gx
                            cy = np.mean([p[1] for p in cluster]) / gy
                            cz = np.mean([p[2] for p in cluster]) / gz
                            mean_niyama = np.mean([self.niyama_calc.niyama_field[p[0], p[1], p[2]] for p in cluster])
                            mean_temp = np.mean([temperature_field[p[0], p[1], p[2]] for p in cluster])

                            severity = self._classify_severity(volume, is_bronze_alloy)
                            defect_type = self._classify_defect_type(volume, is_bronze_alloy)

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
                                "alloy_name": self.niyama_calc.alloy_name,
                                "detected_at": datetime.now(),
                            })

        return self.detected_defects

    def get_critical_defects(self) -> List[Dict]:
        return [d for d in self.detected_defects if d["severity"] in ["high", "critical"]]

    def get_total_shrinkage_volume(self) -> float:
        return sum(d["volume"] for d in self.detected_defects)
