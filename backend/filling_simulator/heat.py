import numpy as np
from typing import Dict, List, Tuple
from common.config_loader import get_thermal_properties, get_grid_size


class HeatTransferSolver:
    def __init__(self, grid_size: Tuple[int, int, int]):
        self.grid_size = grid_size
        thermal_props = get_thermal_properties()
        self.thermal_conductivity = thermal_props["thermal_conductivity"]
        self.density = thermal_props["density"]
        self.specific_heat = thermal_props["specific_heat"]
        self.temperature_field = np.full(grid_size, 25.0, dtype=np.float32)
        self.current_step = 0

    def reset(self, initial_temp: float = 25.0):
        self.temperature_field = np.full(self.grid_size, initial_temp, dtype=np.float32)
        self.current_step = 0

    def step(
        self,
        pouring_temp: float,
        filling_field: List,
        shell_permeability: float,
    ) -> Dict:
        self.current_step += 1
        gx, gy, gz = self.grid_size
        filling_arr = np.array(filling_field, dtype=np.float32)
        dt = 0.01
        alpha = self.thermal_conductivity / (self.density * self.specific_heat)

        new_temp = self.temperature_field.copy()

        for x in range(1, gx - 1):
            for y in range(1, gy - 1):
                for z in range(1, gz - 1):
                    if filling_arr[x, y, z] > 0.1:
                        laplacian = (
                            self.temperature_field[x + 1, y, z]
                            + self.temperature_field[x - 1, y, z]
                            + self.temperature_field[x, y + 1, z]
                            + self.temperature_field[x, y - 1, z]
                            + self.temperature_field[x, y, z + 1]
                            + self.temperature_field[x, y, z - 1]
                            - 6 * self.temperature_field[x, y, z]
                        )
                        source = pouring_temp * filling_arr[x, y, z] * 0.001
                        cooling = (1 - shell_permeability / 100.0) * 0.05
                        new_temp[x, y, z] = (
                            self.temperature_field[x, y, z]
                            + alpha * dt * laplacian
                            + source
                            - cooling * (self.temperature_field[x, y, z] - 25.0)
                        )

        self.temperature_field = new_temp
        points = []
        for x in range(0, gx, 2):
            for y in range(0, gy, 2):
                for z in range(0, gz, 2):
                    points.append({
                        "x": float(x) / gx,
                        "y": float(y) / gy,
                        "z": float(z) / gz,
                        "temperature": float(self.temperature_field[x, y, z]),
                    })

        return {
            "step": self.current_step,
            "points": points,
            "max_temperature": float(np.max(self.temperature_field)),
            "min_temperature": float(np.min(self.temperature_field)),
            "mean_temperature": float(np.mean(self.temperature_field)),
            "temperature_field": self.temperature_field.tolist(),
        }

    def get_temperature_gradient(self) -> np.ndarray:
        gx, gy, gz = self.grid_size
        grad = np.zeros((gx, gy, gz, 3), dtype=np.float32)
        grad[1:-1, :, :, 0] = (self.temperature_field[2:, :, :] - self.temperature_field[:-2, :, :]) / 2.0
        grad[:, 1:-1, :, 1] = (self.temperature_field[:, 2:, :] - self.temperature_field[:, :-2, :]) / 2.0
        grad[:, :, 1:-1, 2] = (self.temperature_field[:, :, 2:] - self.temperature_field[:, :, :-2]) / 2.0
        return grad

    def get_cooling_rate(self, previous_temp_field: np.ndarray, dt: float = 1.0) -> np.ndarray:
        return (previous_temp_field - self.temperature_field) / dt
