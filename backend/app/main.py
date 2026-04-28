from fastapi import FastAPI

from .routers import storage_router, productionorders_router, deliveryorders_router

app = FastAPI()

app.include_router(router=storage_router.router)
app.include_router(router=productionorders_router.router)
app.include_router(router=deliveryorders_router.router)


