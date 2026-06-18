import numpy as np
from typing import Dict, List, Tuple

class FillingSimulationService:
    def __init__(self, grid_size: Tuple[int, int, int] = (20, 20, 20)):
        self.grid_size = grid_size
        self.filling_field = np.zeros(grid_size, dtype=np.float32)
        self.velocity_field = np.zeros(grid_size + (3,), dtype=np.float32)
        self.pressure_field = np.zeros(grid_size, dtype=np.float32)
        self.current_step = 0

    def reset(self):
        self.filling_field = np.zeros(self.grid_size, dtype=np.float32)
        self.velocity_field = np.zeros(self.grid_size + (3,), dtype=np.float32)
        self.pressure_field = np.zeros(self.grid_size, dtype=np.float32)
        self.current_step = 0

    def step(self, filling_ratio_target: float, pouring_temp: float) -> Dict:
        self.current_step += 1
        gx, gy, gz = self.grid_size

        for x in range(gx):
            for y in range(gy):
                for z in range(gz):
                    dist_from_bottom = z / gz if gz > 0 else 0
                    target_fill = filling_ratio_target * (1.0 - 0.3 * np.random.rand())
                    if dist_from_bottom < filling_ratio_target:
                        fill_prob = (filling_ratio_target - dist_from_bottom) / (filling_ratio_target + 0.01)
                        self.filling_field[x, y, z] = min(
                            1.0,
                            self.filling_field[x, y, z] + 0.1 * fill_prob * np.random.rand(),
                        )
                        self.velocity_field[x, y, z, 0] = 0.5 * np.random.randn()
                        self.velocity_field[x, y, z, 1] = 0.5 * np.random.randn()
                        self.velocity_field[x, y, z, 2] = max(0, 0.8 * filling_ratio_target + 0.2 * np.random.rand())
                        self.pressure_field[x, y, z] = (1 - dist_from_bottom) * pouring_temp * 0.001

        current_fill_ratio = float(np.mean(self.filling_field))

        return {
            "step": self.current_step,
            "filling_ratio": current_fill_ratio,
            "mean_velocity": float(np.mean(np.linalg.norm(self.velocity_field, axis=-1))),
            "mean_pressure": float(np.mean(self.pressure_field)),
            "filling_field": self.filling_field.tolist(),
            "velocity_field": self.velocity_field.tolist(),
        }

    def get_filling_ratio(self) -> float:
        return float(np.mean(self.filling_field))

    def get_unfilled_positions(self) -> List[Dict[str, float]]:
        positions = []
        gx, gy, gz = self.grid_size
        threshold = 0.3
        for x in range(gx):
            for y in range(gy):
                for z in range(gz):
                    if self.filling_field[x, y, z] < threshold:
                        positions.append({
                            "x": float(x) / gx,
                            "y": float(y) / gy,
                            "z": float(z) / gz,
                            "filling": float(self.filling_field[x, y, z]),
                        })
        return positions
