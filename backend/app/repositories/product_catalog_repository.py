"""Atomare Übernahme vollständiger SPS-Kataloge und unabhängiger Synchronisationsstatus."""

from datetime import datetime, timezone

from sqlalchemy import Engine, text
from sqlmodel import Session, select

from app.domain.order_run import OrderType
from app.models.order_input import CatalogProduct, OrderCatalog
from app.models.plc_catalog_record import PlcCatalogProductRecord, PlcCatalogStateRecord


class ProductCatalogRepository:
    """Verwendet Produkt-IDs als Identität; historische Auftragsdaten bleiben unverändert."""

    def __init__(self, engine: Engine) -> None:
        """Übernimmt denselben Datenbankzugang wie die bestehende Auftragsverwaltung."""
        self.engine = engine

    def save(self, kind: OrderType, snapshot: OrderCatalog) -> None:
        """Übernimmt einen vollständigen Snapshot atomar und ignoriert verspätete Produktstände."""
        with Session(self.engine) as session, session.begin():
            session.execute(text("SELECT pg_advisory_xact_lock(hashtext('mes-product-catalog'))"))
            rows = list(session.exec(select(PlcCatalogProductRecord)).all())
            newest = max((row.observed_at for row in rows), default=None)
            if newest is None or snapshot.observed_at >= newest:
                existing = {row.product_id: row for row in rows}
                ids = {item.product_id for item in snapshot.products}
                for item in snapshot.products:
                    row = existing.get(item.product_id) or PlcCatalogProductRecord(
                        product_id=item.product_id, product_text=item.product_text,
                        specification={}, observed_at=snapshot.observed_at,
                    )
                    row.product_text = item.product_text
                    row.source_index = item.source_index
                    row.specification = dict(item.specification)
                    row.available = True
                    row.observed_at = snapshot.observed_at
                    session.add(row)
                for row in rows:
                    if row.product_id not in ids:
                        row.available = False
                        session.add(row)
            state = session.get(PlcCatalogStateRecord, kind.value)
            if state is None:
                state = PlcCatalogStateRecord(order_type=kind.value, last_attempt_at=snapshot.observed_at)
            if state.last_success_at is None or snapshot.observed_at >= state.last_success_at:
                state.capacity = snapshot.capacity
                state.last_success_at = snapshot.observed_at
                state.last_attempt_at = snapshot.observed_at
                state.error = None
                session.add(state)

    def read(self, kind: OrderType) -> tuple[OrderCatalog | None, str | None]:
        """Liest einen konsistenten gespeicherten Stand ohne SPS-Verbindung."""
        with Session(self.engine) as session, session.begin():
            session.execute(text("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY"))
            state = session.get(PlcCatalogStateRecord, kind.value)
            products = list(session.exec(select(PlcCatalogProductRecord).where(
                PlcCatalogProductRecord.available.is_(True),
            ).order_by(PlcCatalogProductRecord.product_id)).all())
            if state is None or state.last_success_at is None or state.capacity is None or not products:
                return None, state.error if state else "Der SPS-Produktkatalog wurde noch nicht synchronisiert."
            snapshot = OrderCatalog(
                products=[CatalogProduct(product_id=row.product_id, product_text=row.product_text,
                                         source_index=row.source_index, specification=row.specification) for row in products],
                capacity=state.capacity, observed_at=state.last_success_at,
            )
            return snapshot, state.error

    def failed(self, kind: OrderType, message: str) -> None:
        """Protokolliert einen Fehler, ohne Produkte oder den letzten Erfolgszeitpunkt zu verändern."""
        instant = datetime.now(timezone.utc)
        with Session(self.engine) as session, session.begin():
            session.execute(text("SELECT pg_advisory_xact_lock(hashtext('mes-product-catalog'))"))
            row = session.get(PlcCatalogStateRecord, kind.value)
            if row is None:
                row = PlcCatalogStateRecord(order_type=kind.value, last_attempt_at=instant)
            row.error = message
            row.last_attempt_at = instant
            session.add(row)
