"""FastAPI-Anwendung mit einem gemeinsamen, injizierbaren Auftragsworker."""

from contextlib import asynccontextmanager
import asyncio
import logging
import os
from dataclasses import replace

from fastapi import FastAPI

from app.clients.plc_order_gateway import PlcOrderGateway
from app.db.db import async_session_factory
from app.repositories.order_repository import OrderRepository
from app.routers import storage_router, productionorders_router, deliveryorders_router, orders_router, settings_router
from app.routers.analytics_router import router as analytics_router
from app.services import settings_service
from app.services.analytics import mark_interrupted_runs_unknown
from app.settings import OrderSettings
from app.workers import production_queue, delivery_queue
from app.workers.order_worker_host import OrderWorkerHost
from app.workers.storage_consumer import start_storage_consumer, stop_storage_consumer


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

            async with async_session_factory() as session:
                configured = await settings_service.load_settings(session)
            await asyncio.to_thread(mark_interrupted_runs_unknown)
            base_settings = OrderSettings.from_environment()
            poll_interval = configured.polling_interval_ms / 1000
            settings = replace(
                base_settings,
                poll_interval_s=poll_interval,
                stale_after_s=max(base_settings.stale_after_s, poll_interval * 2),
            )
            host = OrderWorkerHost(
                OrderRepository(engine),
                PlcOrderGateway(os.getenv("OPC_UA_URL", ""), settings_provider=settings_service.get_current_settings),
                settings,
            )
        application.state.order_worker = host
        production_queue.bind_worker(host)
        delivery_queue.bind_worker(host)
        start_storage_consumer()
        await host.start()
        try:
            yield
        finally:
            await host.stop()
            stop_storage_consumer()

    application = FastAPI(lifespan=lifespan)
    for router in (
        storage_router.router, productionorders_router.router,
        deliveryorders_router.router, orders_router.router, settings_router.router,
        analytics_router,
    ):
        application.include_router(router)
    return application


app = create_app()
