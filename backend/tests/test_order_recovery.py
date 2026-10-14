"""Connection-loss tests use simulated PLC state only, never a real server."""

import asyncio
import concurrent.futures
from unittest.mock import AsyncMock

import pytest

from app.clients.execution import OpcUaConnectionError, run_opc
from app.workers import order_execution, plc_handshake, production_queue, delivery_queue
from app.workers.diagnostics import WorkerDiagnostics


@pytest.fixture(autouse=True)
def fast_execution(monkeypatch):
    monkeypatch.setattr(order_execution, "REST_BUFFER_S", 0)
    monkeypatch.setattr(order_execution, "RECONNECT_DELAY_S", 0)
    monkeypatch.setattr(plc_handshake, "POLL_INTERVAL_S", 0)


def payload(module):
    kind = module.DeliveryOrderPayload if module is delivery_queue else module.ProductionOrderPayload
    return kind.model_validate({
        "order_id": "delivery-test-201",
        "mes_auftrag": {
            "kopf": {"Auftragsnummer": 201, "Startdatum": "2026-10-13", "Startzeit": "10:00:00"},
            "inhalt": {"SeriennummerStart": 1002, "Produktqueue": [
                {"ProduktID": 1, "Produkttext": "Salzstreuer, Rot", "Seriennummer": 1002}
            ]},
        },
    })


def test_library_cancellation_is_a_connection_error_not_a_task_shutdown():
    def cancelled_read():
        raise concurrent.futures.CancelledError()

    with pytest.raises(OpcUaConnectionError):
        asyncio.run(run_opc(cancelled_read))


def test_real_task_cancellation_is_not_reconnected():
    async def scenario():
        client = object()
        create = AsyncMock(return_value=client)
        session = order_execution.PlcSession(create, AsyncMock(return_value="SIMULATED"))
        entered = asyncio.Event()

        async def pending_read(*args):
            entered.set()
            await asyncio.Event().wait()

        task = asyncio.create_task(session.wait(pending_read, 10, WorkerDiagnostics(), "waiting"))
        await entered.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        create.assert_awaited_once()

    asyncio.run(scenario())


def test_uncertain_write_without_started_feedback_is_not_replayed(monkeypatch):
    class IdleClient:
        def read_status_mes(self, root, feedback_node=None, status_node=None):
            return 0

        def read_auftragssteuerung(self, root, kopf_node=None, auftragssteuerung_node=None):
            return 0

        async def disconnect(self):
            pass

    async def immediate_start_timeout(client, root, timeout):
        await plc_handshake._wait_for_status(client, root, (1, 5), 0, "start", "Feedback", "StatusMES")

    async def scenario():
        from unittest.mock import MagicMock
        session = order_execution.PlcSession(AsyncMock(return_value=IdleClient()), AsyncMock(return_value="SIMULATED"))
        await session.connect()
        send = AsyncMock(side_effect=OpcUaConnectionError("Write outcome unknown"))
        monkeypatch.setattr(plc_handshake, "wait_for_plc_started", immediate_start_timeout)
        with pytest.raises(TimeoutError, match="start"):
            await order_execution.execute_order(session, payload(delivery_queue), send, WorkerDiagnostics(), MagicMock(), "Delivery")
        send.assert_awaited_once()
        await session.close()

    asyncio.run(scenario())


def test_reconnect_does_not_extend_the_phase_deadline():
    async def scenario():
        async def slow_connect():
            await asyncio.sleep(0.02)
            return object()

        session = order_execution.PlcSession(slow_connect, AsyncMock(return_value="SIMULATED"))
        operation = AsyncMock()
        with pytest.raises(TimeoutError, match="including connection recovery"):
            await session.wait(operation, 0.01, WorkerDiagnostics(), "waiting")
        operation.assert_not_awaited()

    asyncio.run(scenario())
