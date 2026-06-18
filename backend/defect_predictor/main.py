import asyncio
from .service import defect_predictor


async def run_standalone():
    await defect_predictor.initialize()
    print("Defect Predictor service started (standalone mode)")
    print("Waiting for heat simulation results...")

    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        bus = await defect_predictor._bus
        await bus.close()


if __name__ == "__main__":
    asyncio.run(run_standalone())
