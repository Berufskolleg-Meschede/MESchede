"""FastAPI-Anwendung mit einem gemeinsamen, injizierbaren Auftragsworker."""

from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI

from app.clients.plc_order_gateway import PlcOrderGateway
from app.repositories.order_repository import OrderRepository
from app.routers import storage_router, productionorders_router, deliveryorders_router, orders_router
from app.settings import OrderSettings
from app.workers import production_queue, delivery_queue
from app.workers.order_worker_host import OrderWorkerHost


logging.basicConfig(level=logging.INFO)
logging.getLogger("opcua").setLevel(logging.WARNING)


def create_app(worker: OrderWorkerHost | None = None) -> FastAPI:
    """Erlaubt isolierte Testabhängigkeiten ohne eine echte PLC-Verbindung."""

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        """Setzt Services zusammen und beendet den Worker nach auslaufendem I/O."""
        host = worker
        if host is None:
            from app.db.session import engine

            settings = OrderSettings.from_environment()
            host = OrderWorkerHost(
                OrderRepository(engine), PlcOrderGateway(os.getenv("OPC_UA_URL", "")), settings,
            )
        application.state.order_worker = host
        production_queue.bind_worker(host)
        delivery_queue.bind_worker(host)
        await host.start()
        try:
            yield
        finally:
            await host.stop()

    application = FastAPI(lifespan=lifespan)
    for router in (
        storage_router.router, productionorders_router.router,
        deliveryorders_router.router, orders_router.router,
    ):
        application.include_router(router)
    return application


app = create_app()
