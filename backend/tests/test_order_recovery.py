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


@pytest.mark.parametrize("module,queue_name", [(production_queue, "order_queue"), (delivery_queue, "delivery_queue")])
@pytest.mark.parametrize("failure", ["discovery", "idle", "started", "completion", "reset", "count_response", "write_response", "previous_active"])
def test_workers_recover_without_replaying_start(monkeypatch, module, queue_name, failure):
    state = {"command": 1 if failure == "previous_active" else 0,
             "count": 1 if failure == "previous_active" else 0,
             "status": 1 if failure == "previous_active" else 0,
             "failed": False, "starts": 0, "resets": 0, "connections": 0, "root_reads": 0}

    class SimulatedClient:
        async def disconnect(self):
            pass

        def read_status_mes(self, root):
            fail_now = ((failure == "idle" and state["command"] == 0)
                        or (failure == "started" and state["command"] == 1 and state["status"] == 0)
                        or (failure == "completion" and state["command"] == 1 and state["status"] == 1))
            if fail_now and not state["failed"]:
                state["failed"] = True
                raise concurrent.futures.CancelledError()
            if state["command"] == 1:
                state["status"] = 1 if state["status"] == 0 else 5
            return state["status"]

        def read_auftragssteuerung(self, root):
            return state["command"]

        def read_anzahl(self, root):
            return state["count"]

        def clear_product_queue(self, root):
            assert state["status"] == 5

        def write_anzahl(self, root, value):
            assert value == 0 and state["status"] == 5
            state["count"] = 0
            if failure == "count_response" and not state["failed"]:
                state["failed"] = True
                raise concurrent.futures.CancelledError()

        def write_order(self, root, order, kind):
            assert state["status"] == state["command"] == 0
            assert kind == (4 if module is delivery_queue else 1)
            assert len(order.inhalt.Produktqueue) == 1
            state["starts"] += 1
            state["command"] = 1
            state["count"] = len(order.inhalt.Produktqueue)
            if failure == "write_response" and not state["failed"]:
                state["failed"] = True
                raise concurrent.futures.CancelledError()

        def write_auftragssteuerung(self, root, command):
            assert command == 0 and state["status"] == 5 and state["count"] == 0
            state["resets"] += 1
            state["command"] = state["status"] = 0
            if failure == "reset" and not state["failed"]:
                state["failed"] = True
                raise concurrent.futures.CancelledError()

    async def scenario():
        async def create():
            state["connections"] += 1
            return SimulatedClient()

        monkeypatch.setattr(module, "_create_client", create)

        async def get_root(client, node_name):
            state["root_reads"] += 1
            if failure == "discovery" and state["root_reads"] == 2:
                state["failed"] = True
                raise OpcUaConnectionError("Connection lost resolving the current order target")
            return "SIMULATED"

        monkeypatch.setattr(module, "_get_root_node", get_root)
        monkeypatch.setattr(module, "_diagnostics", WorkerDiagnostics())
        queue = asyncio.Queue()
        monkeypatch.setattr(module, queue_name, queue)
        queue.put_nowait(payload(module))
        task = asyncio.create_task(module._worker_loop())
        try:
            await asyncio.wait_for(queue.join(), 3)
            assert not task.done()
            assert state["starts"] == 1
            assert state["resets"] == (2 if failure == "previous_active" else 1)
            assert state["command"] == state["status"] == 0
            assert state["count"] == 0
            assert module._diagnostics.last_completed_order_id == "delivery-test-201"
            assert module._diagnostics.last_error is None
            assert state["connections"] == (1 if failure == "previous_active" else 2)
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(scenario())


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
        def read_status_mes(self, root):
            return 0

        def read_auftragssteuerung(self, root):
            return 0

        async def disconnect(self):
            pass

    async def immediate_start_timeout(client, root, timeout):
        await plc_handshake._wait_for_status(client, root, (1, 5), 0, "start")

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


@pytest.mark.parametrize("module,queue_name", [(production_queue, "order_queue"), (delivery_queue, "delivery_queue")])
@pytest.mark.parametrize("feedback_after_done", [0, 1])
@pytest.mark.parametrize("lost_reply", [None, "queue", "count", "command"])
@pytest.mark.parametrize("completed_at_start", [False, True])
def test_transient_completion_clears_count_then_command_without_awaiting_five_again(
    monkeypatch, module, queue_name, feedback_after_done, lost_reply, completed_at_start
):
    state = {"status": 0, "command": 0, "count": 0, "starts": 0,
             "active_reads": 0, "completed": False, "lost": False, "events": [], "queue_cleared": False}

    class SimulatedClient:
        async def disconnect(self):
            pass

        def read_status_mes(self, root):
            if state["command"] == 1 and not state["completed"]:
                state["active_reads"] += 1
                if state["active_reads"] == (1 if completed_at_start else 2):
                    state["completed"] = True
                    state["status"] = feedback_after_done
                    state["events"].append(("status", 5))
                    return 5  # Only visible once; internal state already changed.
            state["events"].append(("status", state["status"]))
            return state["status"]

        def read_auftragssteuerung(self, root):
            return state["command"]

        def read_anzahl(self, root):
            return state["count"]

        def write_order(self, root, order, kind):
            assert state["command"] == 0
            state["starts"] += 1
            state["command"] = state["status"] = state["count"] = 1

        def lose_response(self, field):
            if field == lost_reply and not state["lost"]:
                state["lost"] = True
                raise concurrent.futures.CancelledError()

        def clear_product_queue(self, root):
            assert state["completed"]
            if not state["queue_cleared"]:
                state["events"].append(("queue", 0))
                state["queue_cleared"] = True
                self.lose_response("queue")

        def write_anzahl(self, root, value):
            assert state["completed"] and state["queue_cleared"] and value == 0
            state["count"] = 0
            state["events"].append(("count", 0))
            self.lose_response("count")

        def write_auftragssteuerung(self, root, value):
            assert state["completed"] and state["count"] == 0 and value == 0
            state["command"] = state["status"] = 0
            state["events"].append(("command", 0))
            self.lose_response("command")

    async def scenario():
        monkeypatch.setattr(module, "_create_client", AsyncMock(side_effect=lambda: SimulatedClient()))
        monkeypatch.setattr(module, "_get_root_node", AsyncMock(return_value="SIMULATED"))
        monkeypatch.setattr(module, "_diagnostics", WorkerDiagnostics())
        queue = asyncio.Queue()
        monkeypatch.setattr(module, queue_name, queue)
        queue.put_nowait(payload(module))
        task = asyncio.create_task(module._worker_loop())
        try:
            await asyncio.wait_for(queue.join(), 3)
            assert not task.done()
            assert state["starts"] == 1
            assert state["count"] == state["command"] == state["status"] == 0
            assert [event for event in state["events"] if event[0] != "status"] == [("queue", 0), ("count", 0), ("command", 0)]
            completed_index = state["events"].index(("status", 5))
            assert state["events"][completed_index + 1] == ("queue", 0)
            assert module._diagnostics.last_completed_order_id == "delivery-test-201"
            assert module._diagnostics.last_error is None
        finally:
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

    asyncio.run(scenario())
