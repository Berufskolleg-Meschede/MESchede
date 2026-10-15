"""Liest den SPS-Produktkatalog einmalig und spiegelt ihn in die konfigurierte Datenbank."""

import asyncio
import json
import logging
import os

from sqlalchemy import create_engine
from sqlmodel import Session

from app.clients.plc_order_gateway import PlcOrderGateway
from app.db.url import get_postgres_url
from app.domain.order_run import OrderType
from app.models.settings import SETTINGS_ID, Settings
from app.repositories.order_repository import OrderRepository
from app.services.order_input_service import OrderInputService
from app.settings import OrderSettings


async def synchronize() -> None:
    """Importiert beide Kapazitäten und den Katalog ohne Dispatch, Start oder SPS-Schreiben."""
    engine = create_engine(get_postgres_url())
    gateway = None
    try:
        with Session(engine) as session:
            configured = session.get(Settings, SETTINGS_ID) or Settings()
        gateway = PlcOrderGateway(os.getenv("OPC_UA_URL", ""), settings_provider=lambda: configured)
        service = OrderInputService(OrderRepository(engine), gateway, OrderSettings.from_environment())
        for kind in OrderType:
            snapshot = await service.synchronize(kind)
            print(json.dumps({
                "order_type": kind.value, "capacity": snapshot.capacity,
                "observed_at": snapshot.observed_at.isoformat(),
                "products": [{"id": item.product_id, "text": item.product_text} for item in snapshot.products],
            }, ensure_ascii=False))
    finally:
        if gateway is not None:
            await gateway.close()
        engine.dispose()


if __name__ == "__main__":
    logging.getLogger("opcua").setLevel(logging.WARNING)
    asyncio.run(synchronize())
