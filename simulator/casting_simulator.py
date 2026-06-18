import requests
import time
import random
import uuid
import math
from datetime import datetime

API_BASE_URL = "http://localhost:8000"
DEFAULT_CASTING_ID = "sim-zunpan-" + uuid.uuid4().hex[:8]


class LostWaxCastingSimulator:
    def __init__(
        self,
        casting_id: str = None,
        api_base: str = API_BASE_URL,
        interval_seconds: int = 60,
        total_steps: int = 60,
    ):
        self.casting_id = casting_id or DEFAULT_CASTING_ID
        self.api_base = api_base.rstrip("/")
        self.interval = interval_seconds
        self.total_steps = total_steps
        self.current_step = 0
        self.wax_temp_base = 60.0
        self.pouring_temp_base = 1180.0
        self.permeability_base = 50.0
        self.running = False

    def create_casting_task(self):
        try:
            resp = requests.post(
                f"{self.api_base}/api/castings",
                json={
                    "name": f"失蜡法模拟铸造-{self.casting_id[-6:]}",
                    "parameters": {
                        "material": "青铜 Cu-Sn 12% Pb 2%",
                        "pouring_temperature_target": self.pouring_temp_base,
                        "wax_pattern_temperature": self.wax_temp_base,
                        "shell_layers": 9,
                        "shell_material": "硅溶胶+石英砂",
                        "simulation": True,
                    },
                },
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.casting_id = data["id"]
                print(f"[OK] Created casting task: {self.casting_id}")
                return True
            print(f"[WARN] Failed to create casting: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"[ERROR] Create casting failed: {e}")
        return False

    def start_simulation(self):
        try:
            resp = requests.post(
                f"{self.api_base}/api/simulation/start",
                json={"casting_id": self.casting_id},
                timeout=5,
            )
            if resp.status_code == 200:
                print(f"[OK] Simulation started for {self.casting_id}")
                return True
        except Exception as e:
            print(f"[ERROR] Start simulation failed: {e}")
        return False

    def _generate_sensor_data(self) -> dict:
        progress_ratio = self.current_step / self.total_steps
        filling_progress = min(100.0, progress_ratio * 100 + random.uniform(-3, 3))

        wax_temp = (
            self.wax_temp_base
            + progress_ratio * 40
            + random.uniform(-2, 4)
            + 10 * math.sin(progress_ratio * math.pi)
        )

        pouring_temp = (
            self.pouring_temp_base
            - progress_ratio * 150
            + random.uniform(-10, 10)
            + 30 * math.sin(progress_ratio * math.pi * 1.5)
        )

        permeability = (
            self.permeability_base
            + random.uniform(-5, 5)
            + 8 * math.sin(progress_ratio * math.pi * 2)
        )

        if self.current_step > self.total_steps * 0.7 and random.random() < 0.2:
            permeability += random.uniform(-15, -5)

        return {
            "casting_id": self.casting_id,
            "timestamp": datetime.now().isoformat(),
            "wax_temperature": round(max(0, wax_temp), 2),
            "pouring_temperature": round(max(0, pouring_temp), 2),
            "shell_permeability": round(max(0, min(100, permeability)), 2),
            "filling_progress": round(max(0, min(100, filling_progress)), 2),
        }

    def send_sensor_data(self, data: dict) -> bool:
        try:
            resp = requests.post(
                f"{self.api_base}/api/sensor/data",
                json=data,
                timeout=5,
            )
            if resp.status_code == 200:
                return True
            print(f"[WARN] Sensor upload failed: {resp.status_code}")
        except Exception as e:
            print(f"[ERROR] Sensor upload error: {e}")
        return False

    def run(self, real_time: bool = True):
        print(f"\n=== 失蜡法铸造模拟器启动 ===")
        print(f"Casting ID: {self.casting_id}")
        print(f"Interval: {self.interval}s, Steps: {self.total_steps}")
        print(f"API: {self.api_base}\n")

        self.create_casting_task()
        self.start_simulation()
        self.running = True

        try:
            for step in range(1, self.total_steps + 1):
                self.current_step = step
                data = self._generate_sensor_data()
                success = self.send_sensor_data(data)

                status_symbol = "✓" if success else "✗"
                print(
                    f"[{step:03d}/{self.total_steps}] {status_symbol}  "
                    f"蜡模={data['wax_temperature']:6.1f}°C  "
                    f"浇铸={data['pouring_temperature']:6.1f}°C  "
                    f"透气={data['shell_permeability']:5.1f}%  "
                    f"充型={data['filling_progress']:5.1f}%"
                )

                if step >= self.total_steps:
                    print("\n[DONE] Simulation complete")
                    break

                if real_time:
                    time.sleep(self.interval)

        except KeyboardInterrupt:
            print("\n[INFO] Simulator interrupted by user")
        finally:
            self.running = False
            try:
                requests.post(f"{self.api_base}/api/simulation/stop", timeout=3)
            except Exception:
                pass


def main():
    import argparse

    parser = argparse.ArgumentParser(description="失蜡法铸造工艺模拟器")
    parser.add_argument("--api", default=API_BASE_URL, help="后端API地址")
    parser.add_argument("--interval", type=int, default=3, help="上报间隔（秒），默认3秒加速演示")
    parser.add_argument("--steps", type=int, default=60, help="总步数")
    parser.add_argument("--fast", action="store_true", help="快速模式（无延迟）")
    parser.add_argument("--casting-id", help="指定铸造任务ID")

    args = parser.parse_args()

    sim = LostWaxCastingSimulator(
        casting_id=args.casting_id,
        api_base=args.api,
        interval_seconds=0 if args.fast else args.interval,
        total_steps=args.steps,
    )
    sim.run(real_time=not args.fast)


if __name__ == "__main__":
    main()
