import asyncio
from .service import dtu_service


async def run_standalone():
    await dtu_service.initialize()
    print("DTU Receiver service started (standalone mode)")
    print("Subscribing to simulation control messages...")

    bus = await dtu_service._bus

    async def handle_control(msg):
        print(f"DTU Received control:", msg)

    await bus.subscribe("simulation_control", handle_control)
    await bus.start_listening()

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await bus.close()


if __name__ == "__main__":
    asyncio.run(run_standalone())
