import asyncio
import json
import os
import threading
from typing import Optional

try:
    import paho.mqtt.client as mqtt
    HAS_MQTT = True
except ImportError:
    HAS_MQTT = False

from .service import dtu_service
from common.redis_bus import get_message_bus

MQTT_HOST = os.environ.get("MQTT_HOST", "localhost")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC", "lwc/sensor/data/#")
MQTT_CLIENT_ID = os.environ.get("MQTT_CLIENT_ID", "dtu-receiver")


class MqttSensorReceiver:
    def __init__(
        self,
        host: str = MQTT_HOST,
        port: int = MQTT_PORT,
        topic: str = MQTT_TOPIC,
        client_id: str = MQTT_CLIENT_ID,
    ):
        self.host = host
        self.port = port
        self.topic = topic
        self.client_id = client_id
        self._client: Optional[mqtt.Client] = None
        self._connected = False
        self._loop_thread: Optional[threading.Thread] = None
        self._running = False
        self._bus = None

    async def initialize(self):
        self._bus = await get_message_bus()

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self._connected = True
            print(f"[MQTT] Connected to {self.host}:{self.port}")
            client.subscribe(self.topic, qos=1)
            print(f"[MQTT] Subscribed to topic: {self.topic}")
        else:
            print(f"[MQTT] Connection failed with code: {rc}")
            self._connected = False

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        print(f"[MQTT] Disconnected from broker (code: {rc})")

    def _on_message(self, client, userdata, msg):
        try:
            payload = msg.payload.decode("utf-8")
            data = json.loads(payload)

            topic_parts = msg.topic.split("/")
            casting_id = topic_parts[-1] if len(topic_parts) > 0 else None

            if casting_id and "casting_id" not in data:
                data["casting_id"] = casting_id

            asyncio.run_coroutine_threadsafe(
                self._handle_sensor_data(data),
                asyncio.get_event_loop(),
            )
        except json.JSONDecodeError as e:
            print(f"[MQTT] Invalid JSON payload: {e}")
        except Exception as e:
            print(f"[MQTT] Error processing message: {e}")

    async def _handle_sensor_data(self, data: dict):
        try:
            result = await dtu_service.process_sensor_data(data)
            if result.get("status") == "ok":
                pass
            else:
                print(f"[MQTT] Sensor data validation failed: {result.get('errors')}")
        except Exception as e:
            print(f"[MQTT] Error handling sensor data: {e}")

    def start(self):
        if not HAS_MQTT:
            print("[WARN] paho-mqtt not installed, MQTT receiver disabled")
            return False

        self._running = True

        self._client = mqtt.Client(client_id=self.client_id, clean_session=True)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        try:
            self._client.connect_async(self.host, self.port, keepalive=60)
            self._client.loop_start()
            print(f"[MQTT] Receiver starting (connecting to {self.host}:{self.port})...")
            return True
        except Exception as e:
            print(f"[MQTT] Failed to start receiver: {e}")
            self._running = False
            return False

    def stop(self):
        self._running = False
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
            print("[MQTT] Receiver stopped")

    @property
    def is_connected(self) -> bool:
        return self._connected and self._running


mqtt_receiver = MqttSensorReceiver()


def start_mqtt_receiver():
    mqtt_receiver.start()
    return mqtt_receiver


def stop_mqtt_receiver():
    mqtt_receiver.stop()
