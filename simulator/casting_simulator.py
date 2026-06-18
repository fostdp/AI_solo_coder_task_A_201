import requests
import time
import random
import uuid
import math
import os
import json
from datetime import datetime
from typing import Optional, Dict

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False

API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "lwc/sensor/data")
DEFAULT_CASTING_ID = "sim-zunpan-" + uuid.uuid4().hex[:8]

SHELL_MATERIALS = {
    "silica_sol": {
        "name": "硅溶胶+石英砂",
        "layers": 9,
        "permeability_base": 50.0,
        "thermal_conductivity": 1.2,
        "strength": "high",
    },
    "water_glass": {
        "name": "水玻璃+石英砂",
        "layers": 7,
        "permeability_base": 35.0,
        "thermal_conductivity": 0.8,
        "strength": "medium",
    },
    "ethyl_silicate": {
        "name": "硅酸乙酯+锆英砂",
        "layers": 10,
        "permeability_base": 65.0,
        "thermal_conductivity": 1.5,
        "strength": "very_high",
    },
    "gypsum": {
        "name": "石膏型",
        "layers": 1,
        "permeability_base": 20.0,
        "thermal_conductivity": 0.5,
        "strength": "low",
    },
}

ALLOY_TYPES = {
    "bronze_cu_sn": {
        "name": "青铜 Cu-Sn 12% Pb 2%",
        "pouring_temp_base": 1180.0,
        "pouring_temp_min": 1120.0,
        "pouring_temp_max": 1250.0,
        "density": 8.7,
        "specific_heat": 0.38,
    },
    "brass": {
        "name": "黄铜 Cu-Zn 30%",
        "pouring_temp_base": 1060.0,
        "pouring_temp_min": 1000.0,
        "pouring_temp_max": 1120.0,
        "density": 8.5,
        "specific_heat": 0.40,
    },
    "stainless_steel": {
        "name": "不锈钢 304",
        "pouring_temp_base": 1580.0,
        "pouring_temp_min": 1520.0,
        "pouring_temp_max": 1650.0,
        "density": 7.9,
        "specific_heat": 0.50,
    },
    "cast_iron": {
        "name": "灰口铸铁 HT200",
        "pouring_temp_base": 1350.0,
        "pouring_temp_min": 1300.0,
        "pouring_temp_max": 1420.0,
        "density": 7.2,
        "specific_heat": 0.46,
    },
    "aluminum_alloy": {
        "name": "铝合金 A356",
        "pouring_temp_base": 720.0,
        "pouring_temp_min": 680.0,
        "pouring_temp_max": 760.0,
        "density": 2.7,
        "specific_heat": 0.96,
    },
}


class LostWaxCastingSimulator:
    def __init__(
        self,
        casting_id: str = None,
        api_base: str = API_BASE_URL,
        interval_seconds: int = 60,
        total_steps: int = 60,
        alloy_type: str = "bronze_cu_sn",
        shell_material: str = "silica_sol",
        pouring_temp: Optional[float] = None,
        shell_layers: Optional[int] = None,
        wax_temp: float = 60.0,
        use_mqtt: bool = False,
        mqtt_host: str = MQTT_HOST,
        mqtt_port: int = MQTT_PORT,
        mqtt_topic: str = MQTT_TOPIC,
        defect_intensity: float = 1.0,
    ):
        self.casting_id = casting_id or DEFAULT_CASTING_ID
        self.api_base = api_base.rstrip("/")
        self.interval = interval_seconds
        self.total_steps = total_steps
        self.current_step = 0
        self.running = False
        self.defect_intensity = defect_intensity

        alloy = ALLOY_TYPES.get(alloy_type, ALLOY_TYPES["bronze_cu_sn"])
        self.alloy_type = alloy_type
        self.alloy_name = alloy["name"]
        self.pouring_temp_base = pouring_temp or alloy["pouring_temp_base"]
        self.pouring_temp_min = alloy["pouring_temp_min"]
        self.pouring_temp_max = alloy["pouring_temp_max"]
        self.alloy_density = alloy["density"]

        shell = SHELL_MATERIALS.get(shell_material, SHELL_MATERIALS["silica_sol"])
        self.shell_material = shell_material
        self.shell_name = shell["name"]
        self.permeability_base = shell["permeability_base"]
        self.thermal_conductivity = shell["thermal_conductivity"]
        self.shell_layers = shell_layers or shell["layers"]
        self.shell_strength = shell["strength"]

        self.wax_temp_base = wax_temp

        self.use_mqtt = use_mqtt
        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_topic = mqtt_topic
        self.mqtt_client = None

        if use_mqtt:
            self._setup_mqtt()

    def _setup_mqtt(self):
        if not HAS_MQTT:
            print("[WARN] paho-mqtt not installed, falling back to HTTP")
            self.use_mqtt = False
            return

        self.mqtt_client = mqtt.Client(client_id=f"simulator-{self.casting_id}")
        try:
            self.mqtt_client.connect(self.mqtt_host, self.mqtt_port, keepalive=60)
            self.mqtt_client.loop_start()
            print(f"[OK] MQTT connected to {self.mqtt_host}:{self.mqtt_port}")
        except Exception as e:
            print(f"[WARN] MQTT connection failed: {e}, falling back to HTTP")
            self.use_mqtt = False
            self.mqtt_client = None

    def create_casting_task(self):
        try:
            resp = requests.post(
                f"{self.api_base}/api/castings",
                json={
                    "name": f"失蜡法模拟铸造-{self.casting_id[-6:]}",
                    "parameters": {
                        "material": self.alloy_name,
                        "alloy_type": self.alloy_type,
                        "pouring_temperature_target": self.pouring_temp_base,
                        "wax_pattern_temperature": self.wax_temp_base,
                        "shell_layers": self.shell_layers,
                        "shell_material": self.shell_name,
                        "shell_thermal_conductivity": self.thermal_conductivity,
                        "shell_strength": self.shell_strength,
                        "alloy_density": self.alloy_density,
                        "defect_intensity": self.defect_intensity,
                        "simulation": True,
                    },
                },
                timeout=5,
            )
            if resp.status_code == 200:
                data = resp.json()
                self.casting_id = data["id"]
                print(f"[OK] Created casting task: {self.casting_id}")
                print(f"     合金: {self.alloy_name}")
                print(f"     浇铸温度: {self.pouring_temp_base}°C")
                print(f"     型壳: {self.shell_name} ({self.shell_layers}层)")
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

        base_temp_drop = 150.0
        layer_factor = 9.0 / self.shell_layers
        conductivity_factor = 1.0 / self.thermal_conductivity
        temp_drop_factor = base_temp_drop * layer_factor * conductivity_factor
        temp_drop_factor = max(50.0, min(temp_drop_factor, 400.0))

        wax_temp = (
            self.wax_temp_base
            + progress_ratio * 40
            + random.uniform(-2, 4)
            + 10 * math.sin(progress_ratio * math.pi)
        )

        pouring_temp = (
            self.pouring_temp_base
            - progress_ratio * temp_drop_factor
            + random.uniform(-10, 10)
            + 30 * math.sin(progress_ratio * math.pi * 1.5)
        )

        permeability_factor = self.permeability_base / 50.0
        permeability = (
            50.0 * permeability_factor
            + random.uniform(-5, 5)
            + 8 * math.sin(progress_ratio * math.pi * 2)
        )

        if self.current_step > self.total_steps * 0.7 and random.random() < 0.2:
            permeability += random.uniform(-15, -5)

        shell_temp = (
            self.wax_temp_base
            + progress_ratio * 200
            + random.uniform(-5, 10)
        )

        return {
            "casting_id": self.casting_id,
            "timestamp": datetime.now().isoformat(),
            "step": self.current_step,
            "alloy_type": self.alloy_type,
            "shell_material": self.shell_material,
            "wax_temperature": round(max(0, wax_temp), 2),
            "pouring_temperature": round(max(0, pouring_temp), 2),
            "shell_temperature": round(max(0, shell_temp), 2),
            "shell_permeability": round(max(0, min(100, permeability)), 2),
            "thermal_conductivity": self.thermal_conductivity,
            "filling_progress": round(max(0, min(100, filling_progress)), 2),
            "filling_rate": round(2.5 * random.uniform(0.9, 1.1), 2),
            "defect_risk_factor": round(0.3 + self.defect_intensity * progress_ratio * 0.5, 3),
        }

    def send_sensor_data_mqtt(self, data: dict) -> bool:
        if not self.mqtt_client:
            return False
        try:
            payload = json.dumps(data)
            result = self.mqtt_client.publish(
                f"{self.mqtt_topic}/{self.casting_id}",
                payload,
                qos=1,
            )
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            print(f"[ERROR] MQTT publish error: {e}")
            return False

    def send_sensor_data_http(self, data: dict) -> bool:
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

    def send_sensor_data(self, data: dict) -> bool:
        if self.use_mqtt:
            return self.send_sensor_data_mqtt(data) or self.send_sensor_data_http(data)
        return self.send_sensor_data_http(data)

    def run(self, real_time: bool = True):
        print(f"\n{'=' * 60}")
        print(f"  失蜡法铸造工艺模拟器 v2.0")
        print(f"{'=' * 60}")
        print(f"  Casting ID   : {self.casting_id}")
        print(f"  合金材料     : {self.alloy_name}")
        print(f"  浇铸温度     : {self.pouring_temp_base}°C (范围: {self.pouring_temp_min}-{self.pouring_temp_max}°C)")
        print(f"  型壳材料     : {self.shell_name}")
        print(f"  型壳层数     : {self.shell_layers}层")
        print(f"  热导率       : {self.thermal_conductivity} W/(m·K)")
        print(f"  透气度基准   : {self.permeability_base}%")
        print(f"  蜡模温度     : {self.wax_temp_base}°C")
        print(f"  缺陷强度因子 : {self.defect_intensity}")
        print(f"  上报间隔     : {self.interval}s")
        print(f"  总步数       : {self.total_steps}")
        print(f"  通信方式     : {'MQTT' if self.use_mqtt else 'HTTP'}")
        print(f"  API 地址     : {self.api_base}")
        print(f"{'=' * 60}\n")

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
                    f"型壳={data['shell_temperature']:5.1f}°C  "
                    f"透气={data['shell_permeability']:5.1f}%  "
                    f"充型={data['filling_progress']:5.1f}%"
                )

                if step >= self.total_steps:
                    print(f"\n[DONE] Simulation complete - {self.total_steps} steps")
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
            if self.mqtt_client:
                self.mqtt_client.loop_stop()
                self.mqtt_client.disconnect()


def main():
    import argparse

    parser = argparse.ArgumentParser(description="失蜡法铸造工艺模拟器 v2.0")
    parser.add_argument("--api", default=API_BASE_URL, help="后端API地址")
    parser.add_argument("--interval", type=int, default=3, help="上报间隔（秒），默认3秒加速演示")
    parser.add_argument("--steps", type=int, default=60, help="总步数")
    parser.add_argument("--fast", action="store_true", help="快速模式（无延迟）")
    parser.add_argument("--casting-id", help="指定铸造任务ID")

    parser.add_argument("--alloy", default="bronze_cu_sn",
                        choices=list(ALLOY_TYPES.keys()),
                        help=f"合金类型 ({', '.join(ALLOY_TYPES.keys())})")
    parser.add_argument("--shell", default="silica_sol",
                        choices=list(SHELL_MATERIALS.keys()),
                        help=f"型壳材料 ({', '.join(SHELL_MATERIALS.keys())})")

    parser.add_argument("--pouring-temp", type=float, help="自定义浇铸温度 (°C)")
    parser.add_argument("--shell-layers", type=int, help="自定义型壳层数")
    parser.add_argument("--wax-temp", type=float, default=60.0, help="蜡模初始温度 (°C)")
    parser.add_argument("--defect-intensity", type=float, default=1.0,
                        help="缺陷强度因子 (0.1-2.0)，越高越容易产生缺陷")

    parser.add_argument("--mqtt", action="store_true", help="使用MQTT上传数据")
    parser.add_argument("--mqtt-host", default=MQTT_HOST, help="MQTT Broker地址")
    parser.add_argument("--mqtt-port", type=int, default=MQTT_PORT, help="MQTT Broker端口")
    parser.add_argument("--mqtt-topic", default=MQTT_TOPIC, help="MQTT主题前缀")

    parser.add_argument("--list-alloys", action="store_true", help="列出所有可用合金")
    parser.add_argument("--list-shells", action="store_true", help="列出所有可用型壳材料")

    args = parser.parse_args()

    if args.list_alloys:
        print("\n可用合金类型:")
        for key, info in ALLOY_TYPES.items():
            print(f"  {key:20s} - {info['name']}, 浇铸温度: {info['pouring_temp_base']}°C")
        print()
        return

    if args.list_shells:
        print("\n可用型壳材料:")
        for key, info in SHELL_MATERIALS.items():
            print(f"  {key:20s} - {info['name']}, 层数: {info['layers']}, 透气度基准: {info['permeability_base']}%")
        print()
        return

    sim = LostWaxCastingSimulator(
        casting_id=args.casting_id,
        api_base=args.api,
        interval_seconds=0 if args.fast else args.interval,
        total_steps=args.steps,
        alloy_type=args.alloy,
        shell_material=args.shell,
        pouring_temp=args.pouring_temp,
        shell_layers=args.shell_layers,
        wax_temp=args.wax_temp,
        use_mqtt=args.mqtt,
        mqtt_host=args.mqtt_host,
        mqtt_port=args.mqtt_port,
        mqtt_topic=args.mqtt_topic,
        defect_intensity=args.defect_intensity,
    )
    sim.run(real_time=not args.fast)


if __name__ == "__main__":
    main()
