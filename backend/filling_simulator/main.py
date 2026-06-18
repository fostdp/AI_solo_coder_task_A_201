import asyncio
from .service import filling_simulator


async def run_standalone():
    await filling_simulator.initialize()
    print("Filling Simulator service started (standalone mode)")
    print("Waiting for sensor data and control messages...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        bus = await filling_simulator._bus
        await bus.close()


if __name__ == "__main__":
    asyncio.run(run_standalone())
