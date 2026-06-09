from fastapi import FastAPI

from .routers import sites_router, storage_router, productionorders_router, deliveryorders_router
from .workers.production_queue import start_worker, stop_worker

app = FastAPI()


@app.on_event("startup")
async def start_background_workers() -> None:
	await start_worker()


@app.on_event("shutdown")
async def stop_background_workers() -> None:
	await stop_worker()

app.include_router(router=sites_router.router)
app.include_router(router=storage_router.router)
app.include_router(router=productionorders_router.router)
app.include_router(router=deliveryorders_router.router)


