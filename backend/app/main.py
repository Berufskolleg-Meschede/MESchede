import logging

from fastapi import FastAPI

from .db.db import async_session_factory
from .routers import storage_router, productionorders_router, deliveryorders_router, settings_router
from .services import settings_service
from .workers.production_queue import start_worker, stop_worker
from .workers.delivery_queue import start_delivery_worker, stop_delivery_worker

logging.basicConfig(level=logging.INFO)
# Keep MES progress visible without logging every OPC UA packet/browse/read.
logging.getLogger("opcua").setLevel(logging.WARNING)

app = FastAPI()


@app.on_event("startup")
async def start_background_workers() -> None:
	async with async_session_factory() as session:
		await settings_service.load_settings(session)
	await start_worker()
	await start_delivery_worker()


@app.on_event("shutdown")
async def stop_background_workers() -> None:
	await stop_worker()
	await stop_delivery_worker()

app.include_router(router=storage_router.router)
app.include_router(router=productionorders_router.router)
app.include_router(router=deliveryorders_router.router)
app.include_router(router=settings_router.router)
