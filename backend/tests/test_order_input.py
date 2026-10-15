"""Erfassungsvertrag mit synthetischem Katalog, ohne Verbindung zur echten Steuerung."""

import asyncio
from datetime import datetime, timezone
from unittest.mock import MagicMock
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError
from opcua import ua

from app.clients.plc_order_gateway import PlcOrderGateway
from app.domain.order_run import OrderType
from app.models.mes_auftrag import AuftragKopf, ProduktDaten
from app.models.order_dto import OrderPayload
from app.models.order_input import CATALOG_BYTE_FIELDS, CATALOG_REAL_FIELDS
from app.services.order_input_service import OrderInputService
from app.settings import OrderSettings
from tests.order_fakes import SimulatedGateway
from tests.test_opc_ua_client import _make_client, _make_mock_node, _make_order_tree
from tests.test_orders_api import client_for


@pytest.mark.parametrize("value", [True, 1.5, "1", -1, 256])
def test_product_id_requires_plc_integer(value):
    """Verhindert boolesche Ersatzwerte, implizite Konvertierung und Werteüberlauf."""
    with pytest.raises(ValidationError):
        ProduktDaten(ProduktID=value)


@pytest.mark.parametrize("values", [
    {"Startzeit": "08:00:00Z"}, {"Startzeit": "08:00:00+02:00"},
    {"Startdatum": "1989-12-31"}, {"Startdatum": "2169-01-01"}, {"Prioritaet": True},
])
def test_header_rejects_values_before_plc_write(values):
    """Validiert Writer-Grenzen bereits am Auftragsvertrag."""
    with pytest.raises(ValidationError):
        AuftragKopf(**{"Auftragsnummer": 1, "Startdatum": "2026-10-14", "Startzeit": "08:00:00", **values})


@pytest.mark.parametrize("identifier", [".", "..", "  queue-status  "])
def test_reserved_ids_cannot_hide_the_order_detail(order_payload, identifier):
    """Verhindert Konflikte mit Browser-Pfadnormalisierung und der Diagnoseroute."""
    body = order_payload().model_dump(mode="json")
    with pytest.raises(ValidationError):
        OrderPayload.model_validate({**body, "order_id": identifier})


def test_input_context_is_read_only_and_suggests_independently(order_repository, order_payload):
    """Gleiche Dezimalvorschläge sind keine Bindung zwischen fachlicher ID und PLC-Nummer."""
    order_repository.admit(OrderType.PRODUCTION, order_payload(7, "1"))
    client, gateway = client_for(order_repository)
    context = client.get("/orders/input-context", params={"order_type": "production"}).json()
    assert context["available"]
    assert context["suggested_order_id"] == "2" and context["suggested_plc_order_number"] == 1
    assert context["capacity"] == 33 and context["products"][0]["product_id"] == 1
    assert gateway.events == [] and gateway.reads == 0
    assert len(order_repository.snapshot().orders) == 1
    assert order_repository.suggest_identifiers(OrderType.DELIVERY) == ("1", 1)


def test_plant_time_is_local_and_has_no_offset(order_repository):
    """Verwendet Anlagenzeitzone statt Browser- oder Hostzeit für die Vorbelegung."""
    instant = datetime(2026, 10, 14, 22, 30, tzinfo=timezone.utc)
    gateway = SimulatedGateway()
    service = OrderInputService(order_repository, gateway, OrderSettings(), clock=lambda: instant)
    service.catalog = MagicMock()
    async def catalog(kind):
        """Erzeugt eine zeitlich passende reine Testbeobachtung."""
        result = await gateway.read_input_catalog(kind)
        return result.model_copy(update={"observed_at": instant})
    service.catalog = catalog
    context = asyncio.run(service.prepare(OrderType.PRODUCTION, True))
    assert context.start_date.isoformat() == "2026-10-15"
    assert context.start_time.isoformat() == "00:30:00" and context.start_time.tzinfo is None


@pytest.mark.parametrize("kind", ["production", "delivery"])
def test_valid_admission_and_complete_detail_without_second_run(order_repository, order_payload, kind):
    """Verfolgt beide POST-Wege einschließlich verlorener Wiederholungsantwort."""
    client, gateway = client_for(order_repository)
    prefix = "/productionorder/" if kind == "production" else "/deliveryorder/"
    body = order_payload().model_dump(mode="json")
    first = client.post(prefix, json=body)
    assert first.status_code == 202
    gateway.catalog_error = OSError("Synthetischer Katalogausfall")
    repeat = client.post(prefix, json=body)
    assert repeat.status_code == 202 and repeat.json() == first.json()
    assert gateway.catalog_reads == 0 and gateway.events == []
    detail = client.get(prefix + body["order_id"]).json()
    assert detail["mes_auftrag"] == body["mes_auftrag"]
    assert "mes_auftrag" not in client.get(prefix).json()["orders"][0]
    body["mes_auftrag"]["kopf"]["Prioritaet"] = 2
    assert client.post(prefix, json=body).status_code == 409
    assert len(order_repository.snapshot().orders) == 1


def test_capacity_and_product_text_are_authoritative(order_repository, order_payload):
    """Ein unveränderter ID-Wert erlaubt keinen unbestätigten Produkttext oder Mengenüberlauf."""
    client, gateway = client_for(order_repository)
    gateway.catalog_capacity = 1
    assert client.post("/orders/catalog/sync", params={"order_type": "production"}).status_code == 200
    response = client.post("/productionorder/", json=order_payload().model_dump(mode="json"))
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "Produktqueue"
    body = order_payload(quantity=1).model_dump(mode="json")
    body["mes_auftrag"]["inhalt"]["Produktqueue"][0]["Produkttext"] = "Anderer Text"
    response = client.post("/productionorder/", json=body)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "ProduktID"
    assert order_repository.snapshot().orders == () and gateway.events == []


def test_concurrent_free_number_suggestions_are_rechecked_at_admission(order_repository, order_payload):
    """Zwei Browser dürfen dieselbe vorgeschlagene PLC-Nummer nicht unter verschiedenen IDs annehmen."""
    client, gateway = client_for(order_repository)
    first = order_payload(7, "first").model_dump(mode="json")
    second = order_payload(7, "second").model_dump(mode="json")
    with client, ThreadPoolExecutor(max_workers=2) as executor:
        statuses = list(executor.map(lambda body: client.post("/productionorder/", json=body).status_code, [first, second]))
    assert sorted(statuses) == [202, 409]
    assert len(order_repository.snapshot().orders) == 1 and gateway.events == []


def test_catalog_failure_blocks_first_admission(order_repository, order_payload):
    """Ein fehlender Katalog wird nicht durch Mock-Produkte oder eine erfolgreiche Nullmenge ersetzt."""
    client, gateway = client_for(order_repository)
    gateway.catalog_error = OSError("Synthetischer Ausfall")
    assert client.post("/orders/catalog/sync", params={"order_type": "production"}).status_code == 503
    context = client.get("/orders/input-context", params={"order_type": "production"}).json()
    assert not context["available"] and context["capacity"] == 33
    assert context["products"][0]["product_id"] == 1
    assert client.post("/productionorder/", json=order_payload().model_dump(mode="json")).status_code == 503
    assert order_repository.snapshot().orders == () and gateway.events == []


def test_serial_range_overflow_is_rejected_before_admission(order_repository, order_payload):
    """Ein gültiger Einzelwert hebt den Überlauf des gesamten Auftragsbereichs nicht auf."""
    client, gateway = client_for(order_repository)
    body = order_payload().model_dump(mode="json")
    body["mes_auftrag"]["inhalt"]["SeriennummerStart"] = 65535
    response = client.post("/productionorder/", json=body)
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"][-1] == "SeriennummerStart"
    assert order_repository.snapshot().orders == () and gateway.events == []


def test_catalog_uses_record_ids_skips_zero_and_counts_contiguous_slots():
    """Ein synthetischer Browsebaum prüft ID-Abgrenzung und Slotlücken ohne PLC-Verbindung."""
    gateway = PlcOrderGateway("unused-test-url")
    client = _make_client()
    root, _, content, _ = _make_order_tree(True, slots=3, numeric_indices=True)
    catalog = _make_mock_node("Produktspezifikation")
    empty = _make_mock_node("0")
    product = _make_mock_node("1")
    product.get_children.return_value = [
        _make_mock_node("ProduktID", 42), _make_mock_node("Produkttext", "Synthetisches Produkt", ua.VariantType.String),
        *[_make_mock_node(name, 0) for name in CATALOG_BYTE_FIELDS],
        *[_make_mock_node(name, 0.0, ua.VariantType.Float) for name in CATALOG_REAL_FIELDS],
    ]
    catalog.get_children.return_value = [empty, product]
    database = _make_mock_node("DB_MES_Schnittstelle")
    database.get_children.return_value = [catalog]
    queue = next(node for node in content if node.get_browse_name().Name == "Produktqueue")
    queue.get_children.return_value = [queue.get_children.return_value[0], queue.get_children.return_value[2]]
    gateway.client = client
    gateway.database = database
    gateway._root = MagicMock(return_value=root)
    try:
        snapshot = asyncio.run(gateway.read_input_catalog(OrderType.PRODUCTION))
        assert snapshot.products[0].product_id == 42 and snapshot.capacity == 1
        empty.get_children.assert_not_called()
        for field in product.get_children.return_value:
            field.set_data_value.assert_not_called()
    finally:
        asyncio.run(gateway.close())
