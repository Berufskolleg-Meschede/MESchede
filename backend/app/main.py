import logging
import asyncio

from fastapi import FastAPI

from .routers import sites_router, storage_router, productionorders_router, deliveryorders_router
from .routers.analytics_router import router as analytics_router
from .workers.production_queue import start_worker, stop_worker
from .workers.delivery_queue import start_delivery_worker, stop_delivery_worker
from .services.analytics import mark_interrupted_runs_unknown

logging.basicConfig(level=logging.INFO)
# Keep MES progress visible without logging every OPC UA packet/browse/read.
logging.getLogger("opcua").setLevel(logging.WARNING)

app = FastAPI()


@app.on_event("startup")
async def start_background_workers() -> None:
	await asyncio.to_thread(mark_interrupted_runs_unknown)
	await start_worker()
	await start_delivery_worker()


@app.on_event("shutdown")
async def stop_background_workers() -> None:
	await stop_worker()
	await stop_delivery_worker()

app.include_router(router=sites_router.router)
app.include_router(router=storage_router.router)
app.include_router(router=productionorders_router.router)
app.include_router(router=deliveryorders_router.router)
app.include_router(router=analytics_router)
