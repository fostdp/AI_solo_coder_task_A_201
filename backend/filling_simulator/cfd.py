import numpy as np
from typing import Dict, List, Tuple, Set
from common.config_loader import get_grid_size, get_casting_config


class AMRGrid:
    def __init__(self, base_size: Tuple[int, int, int], max_level: int = 3):
        self.base_size = base_size
        self.max_level = max_level
        self.refined_cells: Dict[Tuple[int, int, int, int], float] = {}
        self.fine_flags: Dict[Tuple[int, int, int], int] = {}
        self.base_filling = np.zeros(base_size, dtype=np.float32)
        self.base_velocity = np.zeros(base_size + (3,), dtype=np.float32)

    def refine_threshold(self) -> float:
        cfg = get_casting_config()
        return cfg["filling"]["refine_threshold"]

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
