import asyncio
import logging
from unittest.mock import AsyncMock, MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.routers import productionorders_router, deliveryorders_router
from app.workers import production_queue, delivery_queue
from app.workers.diagnostics import WorkerDiagnostics


WORKERS = [
    (production_queue, "order_queue", "_worker_task", "start_worker", "stop_worker", productionorders_router.router, "/productionorder"),
    (delivery_queue, "delivery_queue", "_delivery_worker_task", "start_delivery_worker", "stop_delivery_worker", deliveryorders_router.router, "/deliveryorder"),
]


@pytest.fixture(autouse=True)
def reset_delivery_acceptance(monkeypatch):
    monkeypatch.setattr(delivery_queue, "_accepted_orders", {})


@pytest.mark.parametrize("module,queue_name,task_name,start_name,stop_name,router,prefix", WORKERS)
def test_status_endpoint_reports_worker_stage_without_plc_access(
    monkeypatch, module, queue_name, task_name, start_name, stop_name, router, prefix
):
    diagnostics = WorkerDiagnostics(phase="discovering_nodes", last_error="previous failure")
    monkeypatch.setattr(module, "_diagnostics", diagnostics)
    task = MagicMock()
    task.done.return_value = False
    monkeypatch.setattr(module, task_name, task)
    queue = asyncio.Queue()
    queue.put_nowait("pending")
    monkeypatch.setattr(module, queue_name, queue)
    connect = AsyncMock(side_effect=AssertionError("A status request must not connect to the PLC"))
    monkeypatch.setattr(module, "_create_client", connect)
    app = FastAPI()
    app.include_router(router)

    response = TestClient(app).get(f"{prefix}/queue-status")

    assert response.status_code == 200
    assert response.json()["worker_running"] is True
    assert response.json()["worker_phase"] == "discovering_nodes"
    assert response.json()["queue_size"] == 1
    assert response.json()["last_error"] == "previous failure"
    connect.assert_not_called()


@pytest.mark.parametrize("module,queue_name,task_name,start_name,stop_name,router,prefix", WORKERS)
def test_unhandled_worker_failure_is_logged_and_reported(
    monkeypatch, caplog, module, queue_name, task_name, start_name, stop_name, router, prefix
):
    class BrokenQueue(asyncio.Queue):
        async def get(self):
            raise RuntimeError("queue stopped unexpectedly")

    async def scenario():
        diagnostics = WorkerDiagnostics()
        monkeypatch.setattr(module, "_diagnostics", diagnostics)
        monkeypatch.setattr(module, queue_name, BrokenQueue())
        monkeypatch.setattr(module, task_name, None)
        client = MagicMock()
        client.disconnect = AsyncMock()
        monkeypatch.setattr(module, "_create_client", AsyncMock(return_value=client))
        monkeypatch.setattr(module, "_get_root_node", AsyncMock(return_value="root"))
        with caplog.at_level(logging.ERROR):
            await getattr(module, start_name)()
            task = getattr(module, task_name)
            with pytest.raises(RuntimeError, match="queue stopped unexpectedly"):
                await task
            await asyncio.sleep(0)  # deliver the completion callback
            snapshot = module.get_worker_status()
            assert snapshot["worker_running"] is False
            assert snapshot["worker_phase"] == "failed"
            assert snapshot["last_error"] == "RuntimeError: queue stopped unexpectedly"
        client.disconnect.assert_awaited_once()

    asyncio.run(scenario())
    assert "worker stopped unexpectedly" in caplog.text


@pytest.mark.parametrize("module,queue_name,task_name,start_name,stop_name,router,prefix", WORKERS)
def test_started_and_stopped_worker_liveness_is_reported(
    monkeypatch, module, queue_name, task_name, start_name, stop_name, router, prefix
):
    async def scenario():
        monkeypatch.setattr(module, "_diagnostics", WorkerDiagnostics())
        monkeypatch.setattr(module, task_name, None)
        monkeypatch.setattr(module, queue_name, asyncio.Queue())
        client = MagicMock()
        client.disconnect = AsyncMock()
        monkeypatch.setattr(module, "_create_client", AsyncMock(return_value=client))
        monkeypatch.setattr(module, "_get_root_node", AsyncMock(return_value="root"))
        await getattr(module, start_name)()
        await asyncio.sleep(0)
        assert module.get_worker_status()["worker_running"] is True
        assert module.get_worker_status()["worker_phase"] == "waiting_for_order"
        await getattr(module, stop_name)()
        await asyncio.sleep(0)
        assert module.get_worker_status()["worker_running"] is False
        assert module.get_worker_status()["worker_phase"] == "stopped"

    asyncio.run(scenario())


@pytest.mark.parametrize("module,queue_name,task_name,start_name,stop_name,router,prefix", WORKERS)
def test_http_acceptance_and_status_use_the_same_queue(
    monkeypatch, module, queue_name, task_name, start_name, stop_name, router, prefix
):
    monkeypatch.setattr(module, "_diagnostics", WorkerDiagnostics())
    task = MagicMock()
    task.done.return_value = False
    monkeypatch.setattr(module, task_name, task)
    queue = asyncio.Queue()
    monkeypatch.setattr(module, queue_name, queue)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    body = {
        "order_id": "queue-test",
        "mes_auftrag": {
            "kopf": {"Auftragsnummer": 1, "Startdatum": "2026-10-12", "Startzeit": "09:00:00"},
            "inhalt": {"Produktqueue": [{"ProduktID": 1}]},
        },
    }

    assert client.post(f"{prefix}/", json=body).status_code == 202
    assert client.get(f"{prefix}/queue-status").json()["queue_size"] == 1
    assert queue.get_nowait().order_id == "queue-test"


@pytest.mark.parametrize("module,queue_name,task_name,start_name,stop_name,router,prefix", WORKERS)
def test_stopped_worker_rejects_order_instead_of_silently_accepting(
    monkeypatch, module, queue_name, task_name, start_name, stop_name, router, prefix
):
    monkeypatch.setattr(module, "_diagnostics", WorkerDiagnostics())
    monkeypatch.setattr(module, task_name, None)
    queue = asyncio.Queue()
    monkeypatch.setattr(module, queue_name, queue)
    app = FastAPI()
    app.include_router(router)
    body = {
        "order_id": "queue-test",
        "mes_auftrag": {
            "kopf": {"Auftragsnummer": 1, "Startdatum": "2026-10-12", "Startzeit": "09:00:00"},
            "inhalt": {"Produktqueue": [{"ProduktID": 1}]},
        },
    }

    response = TestClient(app).post(f"{prefix}/", json=body)

    assert response.status_code == 503
    assert "worker is not running" in response.json()["detail"]
    assert queue.qsize() == 0


def test_duplicate_delivery_is_not_enqueued_again_even_after_completion(monkeypatch):
    task = MagicMock()
    task.done.return_value = False
    monkeypatch.setattr(delivery_queue, "_delivery_worker_task", task)
    queue = asyncio.Queue()
    monkeypatch.setattr(delivery_queue, "delivery_queue", queue)
    app = FastAPI()
    app.include_router(deliveryorders_router.router)
    body = {"order_id": "delivery-test-201", "mes_auftrag": {
        "kopf": {"Auftragsnummer": 201, "Startdatum": "2026-10-13", "Startzeit": "10:00:00"},
        "inhalt": {"Produktqueue": [{"ProduktID": 1, "Seriennummer": 1002}]},
    }}
    with TestClient(app) as client:
        assert client.post("/deliveryorder/", json=body).status_code == 202
        queue.get_nowait()
        repeated = client.post("/deliveryorder/", json=body)
        assert repeated.status_code == 202
        assert repeated.json()["duplicate"] is True
        assert queue.qsize() == 0
        body["mes_auftrag"]["inhalt"]["Produktqueue"][0]["Seriennummer"] = 1003
        assert client.post("/deliveryorder/", json=body).status_code == 409
        assert queue.qsize() == 0
