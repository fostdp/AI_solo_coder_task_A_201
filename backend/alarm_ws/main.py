import asyncio
from .engine import alert_engine


async def run_standalone():
    await alert_engine.initialize()
    print("Alarm WS service started (standalone mode)")
    print("Waiting for defect and filling results...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        bus = await alert_engine._bus
        await bus.close()


if __name__ == "__main__":
    asyncio.run(run_standalone())
