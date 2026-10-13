import asyncio
from datetime import date, time
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from app.models.mes_auftrag import AuftragInhalt, AuftragKopf, MESAuftrag, ProduktDaten
from app.models.settings import (
    DEFAULT_DELIVERY_NODE,
    DEFAULT_POLLING_INTERVAL_MS,
    DEFAULT_PRODUCTION_NODE,
    MAX_POLLING_INTERVAL_MS,
    MIN_POLLING_INTERVAL_MS,
    SETTINGS_ID,
    Settings,
    SettingsBase,
)
from app.routers import settings_router
from app.services import settings_service
from app.workers import delivery_queue, plc_handshake, production_queue
from app.workers.delivery_queue import DeliveryOrderPayload
from app.workers.production_queue import ProductionOrderPayload
from app.workers.diagnostics import WorkerDiagnostics


@pytest.fixture(autouse=True)
def isolate_runtime_settings(monkeypatch):
    monkeypatch.setattr(settings_service, "_current", None)
    monkeypatch.setattr(plc_handshake, "POLL_INTERVAL_S", 0.5)


class FakeAsyncSession:
    """Minimal stand-in for the SQLModel AsyncSession, holding one row by id."""

    def __init__(self, existing: Settings | None = None):
        self._store: dict[int, Settings] = {}
        if existing is not None:
            self._store[existing.id] = existing
        self.committed = False

    async def get(self, model, id):
        return self._store.get(id)

    def add(self, obj):
        self._store[obj.id] = obj

    async def commit(self):
        self.committed = True

    async def refresh(self, obj):
        pass


# ── Model validation ─────────────────────────────────────────────────────────

def test_defaults_match_the_currently_hardcoded_opc_ua_browse_names():
    settings = Settings()
    assert settings.opcua_node_production_order == DEFAULT_PRODUCTION_NODE == "MESAuftragProduktion"
    assert settings.opcua_node_delivery_order == DEFAULT_DELIVERY_NODE == "MESAuftragKommissionieren"
    assert settings.polling_interval_ms == DEFAULT_POLLING_INTERVAL_MS == 500


@pytest.mark.parametrize("field", ["opcua_node_production_order", "opcua_node_delivery_order"])
def test_empty_or_blank_node_is_rejected(field):
    with pytest.raises(ValidationError):
        SettingsBase(**{field: "   "})


def test_node_value_is_trimmed():
    settings = SettingsBase(opcua_node_production_order="  Custom  ")
    assert settings.opcua_node_production_order == "Custom"


@pytest.mark.parametrize("value", [MIN_POLLING_INTERVAL_MS - 1, MAX_POLLING_INTERVAL_MS + 1])
def test_interval_outside_bounds_is_rejected(value):
    with pytest.raises(ValidationError):
        SettingsBase(polling_interval_ms=value)


@pytest.mark.parametrize("value", [MIN_POLLING_INTERVAL_MS, MAX_POLLING_INTERVAL_MS])
def test_interval_at_bounds_is_accepted(value):
    settings = SettingsBase(polling_interval_ms=value)
    assert settings.polling_interval_ms == value


# ── settings_service: persistence, reload, runtime effect ───────────────────

def test_load_settings_creates_default_row_when_missing():
    async def scenario():
        session = FakeAsyncSession(existing=None)
        settings = await settings_service.load_settings(session)
        assert settings.id == SETTINGS_ID
        assert session.committed is True
        assert settings_service.get_current_settings() is settings

    asyncio.run(scenario())


def test_load_settings_returns_the_persisted_row_unchanged():
    async def scenario():
        existing = Settings(opcua_node_production_order="Bestehend", polling_interval_ms=750)
        session = FakeAsyncSession(existing=existing)
        settings = await settings_service.load_settings(session)
        assert settings is existing
        assert session.committed is False

    asyncio.run(scenario())


def test_apply_settings_updates_the_plc_handshake_poll_interval(monkeypatch):
    monkeypatch.setattr(plc_handshake, "POLL_INTERVAL_S", 999)
    settings_service.apply_settings(Settings(polling_interval_ms=250))
    assert plc_handshake.POLL_INTERVAL_S == 0.25


# ── settings_router: validation atomicity and the active-order guard ────────

def test_put_settings_persists_confirmed_values_and_updates_the_cache(monkeypatch):
    async def scenario():
        current = Settings(
            opcua_node_production_order="Alt", opcua_node_delivery_order="AltLiefer", polling_interval_ms=500
        )
        session = FakeAsyncSession(existing=current)
        monkeypatch.setattr(production_queue, "get_current_order_id", lambda: None)
        monkeypatch.setattr(delivery_queue, "get_current_delivery_order_id", lambda: None)

        payload = SettingsBase(
            opcua_node_production_order="Neu",
            opcua_node_delivery_order="NeuLiefer",
            polling_interval_ms=1000,
        )
        result = await settings_router.put_settings(payload, session)

        assert result.opcua_node_production_order == "Neu"
        assert session.committed is True
        assert settings_service.get_current_settings().opcua_node_production_order == "Neu"
        assert plc_handshake.POLL_INTERVAL_S == 1.0

    asyncio.run(scenario())


def test_put_settings_rejects_production_node_change_during_an_active_production_order(monkeypatch):
    async def scenario():
        current = Settings(
            opcua_node_production_order="Alt", opcua_node_delivery_order="AltLiefer", polling_interval_ms=500
        )
        session = FakeAsyncSession(existing=current)
        monkeypatch.setattr(production_queue, "get_current_order_id", lambda: "order-1")
        monkeypatch.setattr(delivery_queue, "get_current_delivery_order_id", lambda: None)

        payload = SettingsBase(
            opcua_node_production_order="Neu",
            opcua_node_delivery_order="AltLiefer",
            polling_interval_ms=500,
        )

        with pytest.raises(HTTPException) as exc_info:
            await settings_router.put_settings(payload, session)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail[0]["loc"] == ["body", "opcua_node_production_order"]
        stored = await session.get(Settings, SETTINGS_ID)
        assert stored.opcua_node_production_order == "Alt"

    asyncio.run(scenario())


def test_put_settings_rejects_delivery_node_change_during_an_active_delivery_order(monkeypatch):
    async def scenario():
        current = Settings(
            opcua_node_production_order="Alt", opcua_node_delivery_order="AltLiefer", polling_interval_ms=500
        )
        session = FakeAsyncSession(existing=current)
        monkeypatch.setattr(production_queue, "get_current_order_id", lambda: None)
        monkeypatch.setattr(delivery_queue, "get_current_delivery_order_id", lambda: "delivery-1")

        payload = SettingsBase(
            opcua_node_production_order="Alt",
            opcua_node_delivery_order="NeuLiefer",
            polling_interval_ms=500,
        )

        with pytest.raises(HTTPException) as exc_info:
            await settings_router.put_settings(payload, session)

        assert exc_info.value.status_code == 409
        assert exc_info.value.detail[0]["loc"] == ["body", "opcua_node_delivery_order"]
        stored = await session.get(Settings, SETTINGS_ID)
        assert stored.opcua_node_delivery_order == "AltLiefer"

    asyncio.run(scenario())


def test_put_settings_allows_interval_change_while_an_order_is_active(monkeypatch):
    async def scenario():
        current = Settings(
            opcua_node_production_order="Alt", opcua_node_delivery_order="AltLiefer", polling_interval_ms=500
        )
        session = FakeAsyncSession(existing=current)
        monkeypatch.setattr(production_queue, "get_current_order_id", lambda: "order-1")
        monkeypatch.setattr(delivery_queue, "get_current_delivery_order_id", lambda: "delivery-1")

        payload = SettingsBase(
            opcua_node_production_order="Alt",
            opcua_node_delivery_order="AltLiefer",
            polling_interval_ms=2000,
        )
        result = await settings_router.put_settings(payload, session)

        assert result.polling_interval_ms == 2000

    asyncio.run(scenario())


# ── Workers: the configured node is resolved per order, not cached at connect ─

@pytest.mark.parametrize("module,queue_name,payload_type,setting_field", [
    (production_queue, "order_queue", ProductionOrderPayload, "opcua_node_production_order"),
    (delivery_queue, "delivery_queue", DeliveryOrderPayload, "opcua_node_delivery_order"),
])
@pytest.mark.parametrize("reconnect", [False, True])
def test_workers_refresh_configured_target_per_order_and_pin_it_during_reconnect(
    monkeypatch, module, queue_name, payload_type, setting_field, reconnect
):
    async def scenario():
        queue: asyncio.Queue = asyncio.Queue()
        diagnostics = WorkerDiagnostics()
        monkeypatch.setattr(module, queue_name, queue)
        monkeypatch.setattr(module, "_diagnostics", diagnostics)
        client = MagicMock()
        client.disconnect = AsyncMock()
        monkeypatch.setattr(module, "_create_client", AsyncMock(return_value=client))
        current = Settings(**{setting_field: "StartupNode"})
        monkeypatch.setattr(module, "get_current_settings", lambda: current)
        requested_nodes = []

        async def resolve(client, node_name):
            requested_nodes.append(node_name)
            return node_name

        monkeypatch.setattr(module, "_get_root_node", AsyncMock(side_effect=resolve))
        dispatched = []

        async def execute(session, order, send, diagnostics, logger, kind):
            expected_node = f"CustomNode{order.order_id}"
            assert session.root == expected_node
            if reconnect:
                # Even an external cache change must not redirect an active job.
                setattr(current, setting_field, "ChangedDuringOrder")
                await session.close()
                await session.connect()
                assert session.root == expected_node
            dispatched.append(expected_node)

        monkeypatch.setattr(module, "execute_order", AsyncMock(side_effect=execute))
        task = asyncio.create_task(module._worker_loop())
        try:
            await asyncio.sleep(0)
            assert diagnostics.phase == "waiting_for_order"
            for number in (1, 2):
                setattr(current, setting_field, f"CustomNode{number}")
                queue.put_nowait(payload_type(
                    order_id=str(number),
                    mes_auftrag=MESAuftrag(
                        kopf=AuftragKopf(Auftragsnummer=number, Startdatum=date(2026, 10, 12), Startzeit=time(8)),
                        inhalt=AuftragInhalt(Produktqueue=[ProduktDaten(ProduktID=1)]),
                    ),
                ))
                await asyncio.wait_for(queue.join(), timeout=3)
                assert diagnostics.last_completed_order_id == str(number)
                assert diagnostics.last_error is None
            assert dispatched == ["CustomNode1", "CustomNode2"]
            expected = ["StartupNode", "CustomNode1"]
            if reconnect:
                expected.append("CustomNode1")
            expected.append("CustomNode2")
            if reconnect:
                expected.append("CustomNode2")
            assert requested_nodes == expected
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(scenario())


@pytest.mark.parametrize("module", [production_queue, delivery_queue])
def test_root_resolution_uses_the_requested_browse_name(module):
    client = MagicMock()
    client.find_db_mes_schnittstelle = AsyncMock(return_value="db")
    assert asyncio.run(module._get_root_node(client, "CustomNode")) == client._get_child.return_value
    client._get_child.assert_called_once_with("db", "CustomNode")
