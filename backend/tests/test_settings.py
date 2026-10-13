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
    Settings,
    SettingsBase,
)
from app.routers import settings_router
from app.services import settings_service
from app.workers import delivery_queue, plc_handshake, production_queue
from app.workers.delivery_queue import DeliveryOrderPayload
from app.workers.production_queue import ProductionOrderPayload


@pytest.fixture(autouse=True)
def reset_settings_state():
    settings_service.apply_settings(Settings())


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


# ── settings_service: runtime effect ─────────────────────────────────────────

def test_get_current_settings_defaults_to_hardcoded_values():
    settings = settings_service.get_current_settings()
    assert settings.opcua_node_production_order == DEFAULT_PRODUCTION_NODE
    assert settings.opcua_node_delivery_order == DEFAULT_DELIVERY_NODE
    assert settings.polling_interval_ms == DEFAULT_POLLING_INTERVAL_MS


def test_apply_settings_updates_the_plc_handshake_poll_interval(monkeypatch):
    monkeypatch.setattr(plc_handshake, "POLL_INTERVAL_S", 999)
    settings_service.apply_settings(Settings(polling_interval_ms=250))
    assert plc_handshake.POLL_INTERVAL_S == 0.25


# ── settings_router: validation atomicity and the active-order guard ────────

def test_put_settings_persists_confirmed_values_and_updates_the_cache(monkeypatch):
    async def scenario():
        settings_service.apply_settings(
            Settings(opcua_node_production_order="Alt", opcua_node_delivery_order="AltLiefer", polling_interval_ms=500)
        )
        monkeypatch.setattr(production_queue, "get_current_order_id", lambda: None)
        monkeypatch.setattr(delivery_queue, "get_current_delivery_order_id", lambda: None)

        payload = SettingsBase(
            opcua_node_production_order="Neu",
            opcua_node_delivery_order="NeuLiefer",
            polling_interval_ms=1000,
        )
        result = await settings_router.put_settings(payload)

        assert result.opcua_node_production_order == "Neu"
        assert settings_service.get_current_settings().opcua_node_production_order == "Neu"
        assert plc_handshake.POLL_INTERVAL_S == 1.0

    asyncio.run(scenario())


def test_put_settings_rejects_production_node_change_during_an_active_production_order(monkeypatch):
    async def scenario():
        settings_service.apply_settings(
            Settings(opcua_node_production_order="Alt", opcua_node_delivery_order="AltLiefer", polling_interval_ms=500)
        )
        monkeypatch.setattr(production_queue, "get_current_order_id", lambda: "order-1")
        monkeypatch.setattr(delivery_queue, "get_current_delivery_order_id", lambda: None)

        payload = SettingsBase(
            opcua_node_production_order="Neu",
            opcua_node_delivery_order="AltLiefer",
            polling_interval_ms=500,
        )
        with pytest.raises(HTTPException) as exc_info:
            await settings_router.put_settings(payload)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail[0]["loc"] == ["body", "opcua_node_production_order"]
        assert settings_service.get_current_settings().opcua_node_production_order == "Alt"

    asyncio.run(scenario())


def test_put_settings_rejects_delivery_node_change_during_an_active_delivery_order(monkeypatch):
    async def scenario():
        settings_service.apply_settings(
            Settings(opcua_node_production_order="Alt", opcua_node_delivery_order="AltLiefer", polling_interval_ms=500)
        )
        monkeypatch.setattr(production_queue, "get_current_order_id", lambda: None)
        monkeypatch.setattr(delivery_queue, "get_current_delivery_order_id", lambda: "delivery-1")

        payload = SettingsBase(
            opcua_node_production_order="Alt",
            opcua_node_delivery_order="NeuLiefer",
            polling_interval_ms=500,
        )
        with pytest.raises(HTTPException) as exc_info:
            await settings_router.put_settings(payload)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail[0]["loc"] == ["body", "opcua_node_delivery_order"]
        assert settings_service.get_current_settings().opcua_node_delivery_order == "AltLiefer"

    asyncio.run(scenario())


def test_put_settings_allows_interval_change_while_an_order_is_active(monkeypatch):
    async def scenario():
        settings_service.apply_settings(
            Settings(opcua_node_production_order="Alt", opcua_node_delivery_order="AltLiefer", polling_interval_ms=500)
        )
        monkeypatch.setattr(production_queue, "get_current_order_id", lambda: "order-1")
        monkeypatch.setattr(delivery_queue, "get_current_delivery_order_id", lambda: "delivery-1")

        payload = SettingsBase(
            opcua_node_production_order="Alt",
            opcua_node_delivery_order="AltLiefer",
            polling_interval_ms=2000,
        )
        result = await settings_router.put_settings(payload)

        assert result.polling_interval_ms == 2000

    asyncio.run(scenario())


# ── Workers: the configured node is resolved per order, not cached at connect ─

def test_production_worker_resolves_the_currently_configured_node_per_order(monkeypatch):
    async def scenario():
        queue: asyncio.Queue = asyncio.Queue()
        monkeypatch.setattr(production_queue, "order_queue", queue)
        monkeypatch.setattr(production_queue, "_create_client", AsyncMock(return_value=MagicMock()))
        get_root = AsyncMock(return_value="root")
        monkeypatch.setattr(production_queue, "_get_root_node", get_root)
        monkeypatch.setattr(production_queue, "_wait_for_plc_ready", AsyncMock())
        monkeypatch.setattr(production_queue, "_send_order", AsyncMock())
        monkeypatch.setattr(production_queue, "_wait_for_plc_started", AsyncMock())
        monkeypatch.setattr(production_queue, "_wait_for_plc_done", AsyncMock())
        monkeypatch.setattr(
            production_queue,
            "get_current_settings",
            lambda: Settings(opcua_node_production_order="CustomProdNode"),
        )

        queue.put_nowait(ProductionOrderPayload(
            order_id="1",
            mes_auftrag=MESAuftrag(
                kopf=AuftragKopf(Auftragsnummer=1, Startdatum=date(2026, 10, 12), Startzeit=time(8)),
                inhalt=AuftragInhalt(Produktqueue=[ProduktDaten(ProduktID=1)]),
            ),
        ))
        task = asyncio.create_task(production_queue._worker_loop())
        try:
            await asyncio.wait_for(queue.join(), timeout=15)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        get_root.assert_awaited_once()
        assert get_root.call_args.args[1] == "CustomProdNode"

    asyncio.run(scenario())


def test_delivery_worker_resolves_the_currently_configured_node_per_order(monkeypatch):
    async def scenario():
        queue: asyncio.Queue = asyncio.Queue()
        monkeypatch.setattr(delivery_queue, "delivery_queue", queue)
        monkeypatch.setattr(delivery_queue, "_create_client", AsyncMock(return_value=MagicMock()))
        get_root = AsyncMock(return_value="root")
        monkeypatch.setattr(delivery_queue, "_get_root_node", get_root)
        monkeypatch.setattr(delivery_queue, "_wait_for_plc_ready", AsyncMock())
        monkeypatch.setattr(delivery_queue, "_send_order", AsyncMock())
        monkeypatch.setattr(delivery_queue, "_wait_for_plc_started", AsyncMock())
        monkeypatch.setattr(delivery_queue, "_wait_for_plc_done", AsyncMock())
        monkeypatch.setattr(
            delivery_queue,
            "get_current_settings",
            lambda: Settings(opcua_node_delivery_order="CustomDeliveryNode"),
        )

        queue.put_nowait(DeliveryOrderPayload(
            order_id="1",
            mes_auftrag=MESAuftrag(
                kopf=AuftragKopf(Auftragsnummer=1, Startdatum=date(2026, 10, 12), Startzeit=time(8)),
                inhalt=AuftragInhalt(Produktqueue=[ProduktDaten(ProduktID=1)]),
            ),
        ))
        task = asyncio.create_task(delivery_queue._worker_loop())
        try:
            await asyncio.wait_for(queue.join(), timeout=15)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

        get_root.assert_awaited_once()
        assert get_root.call_args.args[1] == "CustomDeliveryNode"

    asyncio.run(scenario())
