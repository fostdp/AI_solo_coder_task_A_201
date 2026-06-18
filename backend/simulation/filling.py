import numpy as np
from typing import Dict, List, Tuple, Set


class AMRGrid:
    def __init__(self, base_size: Tuple[int, int, int] = (20, 20, 20), max_level: int = 3):
        self.base_size = base_size
        self.max_level = max_level
        self.refined_cells: Dict[Tuple[int, int, int, int], float] = {}
        self.fine_flags: Dict[Tuple[int, int, int], int] = {}
        self.base_filling = np.zeros(base_size, dtype=np.float32)
        self.base_velocity = np.zeros(base_size + (3,), dtype=np.float32)

    def refine_threshold(self) -> float:
        return 0.15

    def detect_front_cells(self) -> Set[Tuple[int, int, int]]:
        gx, gy, gz = self.base_size
        front = set()
        grad_threshold = self.refine_threshold()
        for x in range(gx):
            for y in range(gy):
                for z in range(gz):
                    f0 = self.base_filling[x, y, z]
                    if f0 <= 0.05 or f0 >= 0.95:
                        continue
                    max_grad = 0.0
                    for dx, dy, dz in [
                        (1, 0, 0), (-1, 0, 0),
                        (0, 1, 0), (0, -1, 0),
                        (0, 0, 1), (0, 0, -1),
                    ]:
                        nx, ny, nz = x + dx, y + dy, z + dz
                        if 0 <= nx < gx and 0 <= ny < gy and 0 <= nz < gz:
                            g = abs(self.base_filling[nx, ny, nz] - f0)
                            if g > max_grad:
                                max_grad = g
                    if max_grad > grad_threshold:
                        front.add((x, y, z))
        return front

    def detect_thin_wall_cells(self, shell_geometry: np.ndarray | None = None) -> Set[Tuple[int, int, int]]:
        gx, gy, gz = self.base_size
        thin = set()
        if shell_geometry is None:
            for x in range(gx):
                for y in range(gy):
                    for z in range(gz):
                        dx = min(x, gx - 1 - x)
                        dy = min(y, gy - 1 - y)
                        if dx <= 1 or dy <= 1:
                            if 2 < z < gz - 3:
                                thin.add((x, y, z))
            return thin
        for x in range(gx):
            for y in range(gy):
                for z in range(gz):
                    count = 0
                    for dx in range(-2, 3):
                        nx = x + dx
                        if 0 <= nx < gx and shell_geometry[nx, y, z] > 0.5:
                            count += 1
                    if 0 < count < 3:
                        thin.add((x, y, z))
        return thin

    def update_refinement(self, shell_geometry: np.ndarray | None = None):
        front = self.detect_front_cells()
        thin = self.detect_thin_wall_cells(shell_geometry)
        to_refine = front | thin
        for cell in to_refine:
            self.fine_flags[cell] = self.max_level
        stale = [c for c in self.fine_flags if c not in to_refine]
        for c in stale:
            del self.fine_flags[c]

    def get_subcell_count(self) -> int:
        return len(self.fine_flags) * (2 ** (3 * (self.max_level - 1)))

    def get_value(self, x: float, y: float, z: float, gx: int, gy: int, gz: int) -> float:
        ix, iy, iz = int(x), int(y), int(z)
        ix = max(0, min(gx - 1, ix))
        iy = max(0, min(gy - 1, iy))
        iz = max(0, min(gz - 1, iz))
        level = self.fine_flags.get((ix, iy, iz), 1)
        if level <= 1:
            return float(self.base_filling[ix, iy, iz])
        sub = 2 ** (level - 1)
        fx = int((x - ix) * sub)
        fy = int((y - iy) * sub)
        fz = int((z - iz) * sub)
        fx = max(0, min(sub - 1, fx))
        fy = max(0, min(sub - 1, fy))
        fz = max(0, min(sub - 1, fz))
        key = (ix, iy, iz, fx * sub * sub + fy * sub + fz)
        return self.refined_cells.get(key, float(self.base_filling[ix, iy, iz]))

    def set_value(self, x: int, y: int, z: int, val: float, sub_idx: int | None = None):
        if sub_idx is None:
            self.base_filling[x, y, z] = np.float32(val)
            level = self.fine_flags.get((x, y, z), 1)
            if level > 1:
                sub = 2 ** (level - 1)
                sub_total = sub * sub * sub
                for s in range(sub_total):
                    self.refined_cells[(x, y, z, s)] = val
        else:
            self.refined_cells[(x, y, z, sub_idx)] = val


class FillingSimulationService:
    def __init__(self, grid_size: Tuple[int, int, int] = (20, 20, 20), enable_amr: bool = True):
        self.grid_size = grid_size
        self.enable_amr = enable_amr
        self.amr = AMRGrid(grid_size, max_level=3)
        self.filling_field = self.amr.base_filling
        self.velocity_field = np.zeros(grid_size + (3,), dtype=np.float32)
        self.pressure_field = np.zeros(grid_size, dtype=np.float32)
        self.current_step = 0
        self.front_positions: List[Dict[str, float]] = []

    def reset(self):
        self.amr = AMRGrid(self.grid_size, max_level=3)
        self.filling_field = self.amr.base_filling
        self.velocity_field = np.zeros(self.grid_size + (3,), dtype=np.float32)
        self.pressure_field = np.zeros(self.grid_size, dtype=np.float32)
        self.current_step = 0
        self.front_positions = []

    def _apply_amr_fill(self, x: int, y: int, z: int, base_delta: float, target_ratio: float):
        level = self.amr.fine_flags.get((x, y, z), 1)
        if level <= 1:
            self.filling_field[x, y, z] = min(
                np.float32(1.0),
                self.filling_field[x, y, z] + np.float32(base_delta),
            )
            return
        sub = 2 ** (level - 1)
        sub_total = sub * sub * sub
        center_sx, center_sy, center_sz = sub // 2, sub // 2, sub // 2
        for sx in range(sub):
            for sy in range(sub):
                for sz in range(sub):
                    dx = abs(sx - center_sx) / max(sub, 1)
                    dy = abs(sy - center_sy) / max(sub, 1)
                    dz = abs(sz - center_sz) / max(sub, 1)
                    dist = np.sqrt(dx * dx + dy * dy + dz * dz)
                    weight = max(0.0, 1.0 - dist) * target_ratio
                    idx = sx * sub * sub + sy * sub + sz
                    prev = self.amr.refined_cells.get((x, y, z, idx), self.filling_field[x, y, z])
                    self.amr.refined_cells[(x, y, z, idx)] = min(1.0, prev + base_delta * 0.25 * weight)
        sub_vals = [self.amr.refined_cells[(x, y, z, s)] for s in range(sub_total)]
        if sub_vals:
            self.filling_field[x, y, z] = np.float32(np.mean(sub_vals))

    def step(self, filling_ratio_target: float, pouring_temp: float) -> Dict:
        self.current_step += 1
        gx, gy, gz = self.grid_size

        if self.enable_amr:
            self.amr.update_refinement()

        self.front_positions = []
        for x in range(gx):
            for y in range(gy):
                for z in range(gz):
                    dist_from_bottom = z / gz if gz > 0 else 0
                    if dist_from_bottom >= filling_ratio_target:
                        continue
                    fill_prob = (filling_ratio_target - dist_from_bottom) / (filling_ratio_target + 0.01)
                    base_delta = 0.1 * fill_prob * (0.7 + 0.3 * np.random.rand())

                    is_front = False
                    if self.enable_amr:
                        for dx, dy, dz in [
                            (1, 0, 0), (-1, 0, 0),
                            (0, 1, 0), (0, -1, 0),
                            (0, 0, 1), (0, 0, -1),
                        ]:
                            nx, ny, nz = x + dx, y + dy, z + dz
                            if 0 <= nx < gx and 0 <= ny < gy and 0 <= nz < gz:
                                if self.filling_field[nx, ny, nz] < 0.3:
                                    is_front = True
                                    break

                    if self.enable_amr and is_front and (x, y, z) in self.amr.fine_flags:
                        self._apply_amr_fill(x, y, z, base_delta, filling_ratio_target)
                    else:
                        self.filling_field[x, y, z] = min(
                            np.float32(1.0),
                            self.filling_field[x, y, z] + np.float32(base_delta),
                        )

                    if self.filling_field[x, y, z] > 0.1:
                        self.velocity_field[x, y, z, 0] = np.float32(0.5 * np.random.randn())
                        self.velocity_field[x, y, z, 1] = np.float32(0.5 * np.random.randn())
                        self.velocity_field[x, y, z, 2] = np.float32(
                            max(0, 0.8 * filling_ratio_target + 0.2 * np.random.rand())
                        )
                        self.pressure_field[x, y, z] = np.float32(
                            (1 - dist_from_bottom) * pouring_temp * 0.001
                        )

                    if 0.1 < self.filling_field[x, y, z] < 0.9:
                        self.front_positions.append({
                            "x": float(x) / gx,
                            "y": float(y) / gy,
                            "z": float(z) / gz,
                            "fill": float(self.filling_field[x, y, z]),
                        })

        current_fill_ratio = float(np.mean(self.filling_field))

        refined_count = len(self.amr.fine_flags) if self.enable_amr else 0
        subcell_count = self.amr.get_subcell_count() if self.enable_amr else 0

        return {
            "step": self.current_step,
            "filling_ratio": current_fill_ratio,
            "mean_velocity": float(np.mean(np.linalg.norm(self.velocity_field, axis=-1))),
            "mean_pressure": float(np.mean(self.pressure_field)),
            "filling_field": self.filling_field.tolist(),
            "velocity_field": self.velocity_field.tolist(),
            "amr": {
                "enabled": self.enable_amr,
                "refined_cells": refined_count,
                "subcell_count": subcell_count,
                "max_level": self.amr.max_level,
                "front_cells": len(self.front_positions),
            },
            "front_positions": self.front_positions,
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
