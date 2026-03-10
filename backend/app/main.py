from fastapi import FastAPI

from .routers import sites_router, storage_router, productionorders_router, deliveryorders_router
from .db.db import init_db

app = FastAPI()

app.include_router(router=sites_router.router)
app.include_router(router=storage_router.router)
app.include_router(router=productionorders_router.router)
app.include_router(router=sites_router.router)

@app.on_event("startup")
async def startup():
    await init_db()

