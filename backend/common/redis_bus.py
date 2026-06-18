import json
import asyncio
from typing import Dict, Any, Callable, Optional
from common.config_loader import get_redis_connection_params, get_redis_channel

try:
    import redis.asyncio as redis_async
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False


class RedisPubSubBus:
    def __init__(self):
        self._client: Optional[redis_async.Redis] = None
        self._pubsub: Optional[redis_async.client.PubSub] = None
        self._handlers: Dict[str, Callable] = {}
        self._listen_task: Optional[asyncio.Task] = None

    async def connect(self):
        if not HAS_REDIS:
            print("Warning: redis-py not installed, using in-process message bus")
            self._client = None
            return
        params = get_redis_connection_params()
        self._client = redis_async.Redis(**params, decode_responses=True)
        self._pubsub = self._client.pubsub()

    async def close(self):
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        if self._pubsub:
            await self._pubsub.close()
        if self._client:
            await self._client.close()

    async def publish(self, channel_key: str, message: Dict[str, Any]):
        channel = get_redis_channel(channel_key)
        payload = json.dumps(message, ensure_ascii=False, default=str)
        if self._client:
            await self._client.publish(channel, payload)

    async def subscribe(self, channel_key: str, handler: Callable[[Dict[str, Any]], None]):
        self._handlers[channel_key] = handler
        if self._pubsub:
            channel = get_redis_channel(channel_key)
            await self._pubsub.subscribe(channel)

    async def start_listening(self):
        if not self._pubsub or not self._handlers:
            return

        async def _listen():
            async for message in self._pubsub.listen():
                if message["type"] != "message":
                    continue
                channel_name = message["channel"]
                data = json.loads(message["data"])
                for key, handler in self._handlers.items():
                    if get_redis_channel(key) == channel_name:
                        try:
                            if asyncio.iscoroutinefunction(handler):
                                await handler(data)
                            else:
                                handler(data)
                        except Exception as e:
                            print(f"Error handling message on {channel_name}: {e}")

        self._listen_task = asyncio.create_task(_listen())


class InProcessMessageBus:
    def __init__(self):
        self._handlers: Dict[str, list] = {}

    async def connect(self):
        pass

    async def close(self):
        self._handlers.clear()

    async def publish(self, channel_key: str, message: Dict[str, Any]):
        handlers = self._handlers.get(channel_key, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(message)
                else:
                    handler(message)
            except Exception as e:
                print(f"Error handling message on {channel_key}: {e}")

    async def subscribe(self, channel_key: str, handler: Callable[[Dict[str, Any]], None]):
        if channel_key not in self._handlers:
            self._handlers[channel_key] = []
        self._handlers[channel_key].append(handler)

    async def start_listening(self):
        pass


_message_bus: Optional[RedisPubSubBus | InProcessMessageBus] = None


async def get_message_bus() -> RedisPubSubBus | InProcessMessageBus:
    global _message_bus
    if _message_bus is None:
        if HAS_REDIS:
            _message_bus = RedisPubSubBus()
        else:
            _message_bus = InProcessMessageBus()
        await _message_bus.connect()
    return _message_bus
