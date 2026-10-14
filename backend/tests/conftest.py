"""Isolierte PostgreSQL-Schemas für opt-in Integrationsprüfungen."""

import os
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlmodel import SQLModel

import app.models
from app.repositories.order_repository import OrderRepository


def pytest_addoption(parser):
    """Erlaubt eine explizite isolierte Datenbank ohne Laden der Projektkonfiguration."""
    parser.addoption("--order-test-db-url", default=None)


@pytest.fixture
def isolated_postgres_engine(request):
    """Verwendet ausschließlich die explizite Test-URL, niemals die Projekt-env-Dateien."""
    url = request.config.getoption("--order-test-db-url") or os.getenv("TEST_ORDER_DATABASE_URL")
    if not url:
        pytest.skip("PostgreSQL-Test benötigt TEST_ORDER_DATABASE_URL; kein Zugriff auf Projektdaten.")
    schema = "issue29_" + uuid4().hex
    admin = create_engine(url)
    with admin.begin() as connection:
        connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    try:
        yield engine
    finally:
        engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def order_engine(isolated_postgres_engine):
    """Erzeugt nur die Auftragsdomäne im isolierten Schema."""
    engine = isolated_postgres_engine
    names = {"mes_order", "order_run", "product_unit", "run_review", "dispatch_state", "plc_source_state"}
    tables = [table for table in SQLModel.metadata.sorted_tables if table.name in names]
    SQLModel.metadata.create_all(engine, tables=tables)
    return engine


@pytest.fixture
def order_repository(order_engine):
    """Stellt einen neu initialisierten Repository mit echten PostgreSQL-Locks bereit."""
    repository = OrderRepository(order_engine)
    repository.initialize()
    return repository


@pytest.fixture
def order_payload():
    """Liefert PLC-nahe Testaufträge ohne echten Anlagenzugriff."""
    from app.models.order_dto import OrderPayload

    def create(number=1, order_id=None, quantity=2):
        """Erzeugt eindeutig nummerierte geplante Produkteinheiten."""
        return OrderPayload.model_validate({
            "order_id": order_id or f"test-{number}",
            "mes_auftrag": {
                "kopf": {"Auftragsnummer": number, "Startdatum": "2026-10-13", "Startzeit": "08:00:00"},
                "inhalt": {"Produktqueue": [
                    {"ProduktID": 1, "Produkttext": "Testprodukt", "Seriennummer": index + 10,
                     "Sequenznummer": index + 1} for index in range(quantity)
                ]},
            },
        })

    return create
