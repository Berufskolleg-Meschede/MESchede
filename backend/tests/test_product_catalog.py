"""Persistenz und Fehlergrenzen des Katalogspiegels ohne Anlagenzugriff."""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, select
from sqlalchemy.exc import SQLAlchemyError

from app.domain.order_run import OrderType
from app.models.order_input import CatalogProduct, OrderCatalog
from app.models.plc_catalog_record import PlcCatalogProductRecord
from app.repositories.product_catalog_repository import ProductCatalogRepository
from app.services.order_input_service import OrderInputService
from app.settings import OrderSettings
from app.workers.order_worker_host import OrderWorkerHost
from tests.order_fakes import FakeLeadership, SimulatedGateway
from tests.test_orders_api import client_for


def snapshot(instant, text="Produkt A", ids=(1, 2)):
    """Erzeugt vollständige synthetische Katalogstände mit Bauplandaten."""
    return OrderCatalog(observed_at=instant, capacity=33, products=[
        CatalogProduct(product_id=value, product_text=f"{text} {value}", source_index=value,
                       specification={"Gehaeuse": 2, "GewichtMax": 3.5}) for value in ids
    ])


def test_catalog_persists_updates_and_deactivates_without_deleting(order_engine):
    """Ein erneuter Repository liest denselben Stand; entfernte IDs bleiben historisch erhalten."""
    repository = ProductCatalogRepository(order_engine)
    instant = datetime.now(timezone.utc)
    first = snapshot(instant)
    repository.save(OrderType.PRODUCTION, first)
    repository.save(OrderType.PRODUCTION, first)
    stored, error = ProductCatalogRepository(order_engine).read(OrderType.PRODUCTION)
    assert stored == first and error is None
    newer = snapshot(instant + timedelta(seconds=1), "Umbenannt", (2,))
    repository.save(OrderType.PRODUCTION, newer)
    assert repository.read(OrderType.PRODUCTION)[0] == newer
    repository.save(OrderType.PRODUCTION, first)
    assert repository.read(OrderType.PRODUCTION)[0] == newer
    with Session(order_engine) as session:
        rows = list(session.exec(select(PlcCatalogProductRecord)).all())
        assert len(rows) == 2
        assert not session.get(PlcCatalogProductRecord, 1).available
        assert session.get(PlcCatalogProductRecord, 2).specification["GewichtMax"] == 3.5


def test_failed_sync_preserves_last_success_and_no_start(order_repository):
    """Ein Lesefehler erhält gespeicherte Produkte, sperrt neue Annahmen und schreibt keine SPS-Werte."""
    gateway = SimulatedGateway()
    service = OrderInputService(order_repository, gateway, OrderSettings())
    asyncio.run(service.synchronize(OrderType.PRODUCTION))
    before, error = service.catalog_repository.read(OrderType.PRODUCTION)
    assert error is None
    gateway.catalog_error = OSError("synthetischer Ausfall")
    with pytest.raises(OSError):
        asyncio.run(service.synchronize(OrderType.PRODUCTION))
    after, error = service.catalog_repository.read(OrderType.PRODUCTION)
    assert after == before and error
    with pytest.raises(ValueError):
        asyncio.run(service.catalog(OrderType.PRODUCTION))
    assert gateway.events == [] and order_repository.snapshot().orders == ()


def test_stale_catalog_stays_visible_but_cannot_be_used(order_repository):
    """Frischegrenze gilt unabhängig von den Live-Auftragsstatusintervallen."""
    instant = datetime.now(timezone.utc)
    service = OrderInputService(order_repository, SimulatedGateway(), OrderSettings(),
                                clock=lambda: instant + timedelta(seconds=301))
    service.catalog_repository.save(OrderType.DELIVERY, snapshot(instant))
    context = asyncio.run(service.prepare(OrderType.DELIVERY, True))
    assert not context.available and len(context.products) == 2 and context.capacity == 33


def test_order_capacities_are_stored_independently(order_engine):
    """Beide Arten teilen Produkte, behalten aber ihren eigenen bestätigten Slotumfang."""
    repository = ProductCatalogRepository(order_engine)
    instant = datetime.now(timezone.utc)
    repository.save(OrderType.PRODUCTION, snapshot(instant))
    repository.save(OrderType.DELIVERY, snapshot(instant).model_copy(update={"capacity": 12}))
    assert repository.read(OrderType.PRODUCTION)[0].capacity == 33
    assert repository.read(OrderType.DELIVERY)[0].capacity == 12


def test_background_catalog_uses_dedicated_gateway_and_closes_it(order_repository):
    """Ein blockierter Katalogzugriff verzögert die Beobachtung von Aufträgen nicht."""
    class SlowCatalog(SimulatedGateway):
        """Wartet kontrolliert auf Abbruch statt auf eine reale SPS."""

        async def read_input_catalog(self, kind):
            """Lässt den Abgleich bis zum Shutdown offen."""
            self.catalog_reads += 1
            await asyncio.Event().wait()

    async def scenario():
        """Beobachtet beide getrennten Tasks und deren geordnetes Ende."""
        orders, catalog = SimulatedGateway(), SlowCatalog()
        host = OrderWorkerHost(order_repository, orders, OrderSettings(), FakeLeadership(), catalog_gateway=catalog)
        await host.start()
        try:
            for _ in range(100):
                if orders.reads >= 2 and catalog.catalog_reads:
                    break
                await asyncio.sleep(0.01)
            assert orders.reads >= 2 and orders.catalog_reads == 0
            assert catalog.catalog_reads == 1 and catalog.events == []
        finally:
            await host.stop()
        assert orders.closed and catalog.closed and host.catalog_task.done()

    asyncio.run(scenario())


def test_database_catalog_failure_returns_unavailable(order_repository, order_payload, monkeypatch):
    """Eine fehlgeschlagene DB-Lesung wird als 503 gemeldet und erzeugt keinen Auftrag."""
    client, gateway = client_for(order_repository)

    async def fail(kind):
        """Simuliert ausschließlich den Katalog-DB-Ausfall nach der Identitätsprüfung."""
        raise SQLAlchemyError("synthetischer Datenbankausfall")

    monkeypatch.setattr(client.app.state.order_worker.input_service, "catalog", fail)
    assert client.post("/productionorder/", json=order_payload().model_dump(mode="json")).status_code == 503
    assert order_repository.snapshot().orders == () and gateway.catalog_reads == 0
