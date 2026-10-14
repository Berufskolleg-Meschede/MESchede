"""Diagnosen und HTTP-Annahme des gemeinsamen, dauerhaft speichernden Workers."""

import asyncio
import logging
from unittest.mock import MagicMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.domain.order_run import OrderType
from app.routers import productionorders_router, deliveryorders_router
from app.settings import OrderSettings
from app.workers.order_worker_host import OrderWorkerHost
from tests.order_fakes import FakeLeadership, SimulatedGateway


@pytest.mark.parametrize("kind,router,prefix", [
    (OrderType.PRODUCTION, productionorders_router.router, "/productionorder"),
    (OrderType.DELIVERY, deliveryorders_router.router, "/deliveryorder"),
])
def test_status_endpoint_reports_worker_stage_without_plc_access(order_repository, kind, router, prefix):
    """GET liest gespeicherte Diagnosen und verbindet nicht zur Anlage."""
    gateway = SimulatedGateway()
    host = OrderWorkerHost(order_repository, gateway, OrderSettings(), FakeLeadership())
    host.phase = "discovering_nodes"
    host.task = MagicMock()
    host.task.done.return_value = False
    app = FastAPI()
    app.state.order_worker = host
    app.include_router(router)
    response = TestClient(app).get(prefix + "/queue-status")
    assert response.status_code == 200
    assert response.json()["worker_phase"] == "discovering_nodes"
    assert response.json()["worker_running"]
    assert gateway.reads == 0


def test_unhandled_worker_failure_is_logged_and_reported(order_repository, caplog):
    """Ein echter Taskausstieg wird sofort in Diagnose und Log sichtbar."""
    class BrokenGateway(SimulatedGateway):
        """Verursacht einen unerwarteten Fehler an der technischen Grenze."""

        async def read(self, kind):
            """Erzeugt den isolierten Fehler ohne echte PLC."""
            raise RuntimeError("Testworker unerwartet beendet")

    async def scenario():
        """Beobachtet den Ausstieg einschließlich Cleanup und Callback."""
        host = OrderWorkerHost(order_repository, BrokenGateway(), OrderSettings(), FakeLeadership())
        with caplog.at_level(logging.ERROR):
            await host.start()
            with pytest.raises(RuntimeError, match="Testworker"):
                await host.task
            await asyncio.sleep(0)
            assert not host.running
            assert host.phase == "failed"
            assert "Testworker" in host.last_error

    asyncio.run(scenario())
    assert "Auftragsworker wurde unerwartet beendet" in caplog.text


def test_started_and_stopped_worker_liveness_is_reported(order_repository):
    """Liveness folgt dem tatsächlichen Task; Stop beendet beide Ressourcen."""
    async def scenario():
        """Startet ausschließlich den injizierten Simulator."""
        gateway = SimulatedGateway()
        leadership = FakeLeadership()
        host = OrderWorkerHost(order_repository, gateway, OrderSettings(), leadership)
        await host.start()
        assert host.running
        await asyncio.sleep(0.02)
        await host.stop()
        assert not host.running
        assert gateway.closed and leadership.closed

    asyncio.run(scenario())


@pytest.mark.parametrize("kind,router,prefix", [
    (OrderType.PRODUCTION, productionorders_router.router, "/productionorder"),
    (OrderType.DELIVERY, deliveryorders_router.router, "/deliveryorder"),
])
def test_http_acceptance_and_status_use_the_same_queue(order_repository, order_payload, kind, router, prefix):
    """HTTP-Annahme, Bereichsliste und Diagnose haben dieselbe dauerhafte Quelle."""
    host = OrderWorkerHost(order_repository, SimulatedGateway(), OrderSettings(), FakeLeadership())
    host.task = MagicMock()
    host.task.done.return_value = False
    app = FastAPI()
    app.state.order_worker = host
    app.include_router(router)
    client = TestClient(app)
    payload = order_payload().model_dump(mode="json")
    accepted = client.post(prefix + "/", json=payload)
    assert accepted.status_code == 202
    assert client.get(prefix + "/queue-status").json()["queue_size"] == 1
    assert client.get(prefix + "/").json()["orders"][0]["run_id"] == accepted.json()["run_id"]
    assert len(order_repository.snapshot().orders) == 1


@pytest.mark.parametrize("router,prefix", [
    (productionorders_router.router, "/productionorder"),
    (deliveryorders_router.router, "/deliveryorder"),
])
def test_stopped_worker_rejects_order_instead_of_silently_accepting(order_repository, order_payload, router, prefix):
    """Ein tatsächlich gestoppter Worker bestätigt keinen Auftrag."""
    host = OrderWorkerHost(order_repository, SimulatedGateway(), OrderSettings(), FakeLeadership())
    app = FastAPI()
    app.state.order_worker = host
    app.include_router(router)
    response = TestClient(app).post(prefix + "/", json=order_payload().model_dump(mode="json"))
    assert response.status_code == 503
    assert order_repository.snapshot().orders == ()
