"""Wiederanlauf, parallele Reviews und Führungswechsel mit realen DB-Locks."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import json
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import text

from app.domain.order_run import OrderConflict, OrderType, RunPhase
from app.models.order_dto import ReviewRequest
from app.repositories.worker_leadership import WorkerLeadership
from app.services.order_dispatch_service import OrderDispatchService
from app.services.order_recovery_service import OrderRecoveryService
from app.services.product_result_service import ProductResultService
from app.services.order_query_service import OrderQueryService
from app.services.run_review_service import RunReviewService
from app.settings import OrderSettings
from tests.order_fakes import FakeLeadership, SimulatedGateway
from tests.test_order_services import finished_snapshot, running_order


SETTINGS = OrderSettings(contract_verified=True, product_results={11: 'good', 12: 'failed'}, rest_buffer_s=0)


def test_unknown_verified_product_codes_keep_quantities_unknown(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    ProductResultService(order_repository, SETTINGS).observe(stored.run.id, finished_snapshot(order_repository, statuses=(99,99)))
    view = OrderQueryService(order_repository, SETTINGS).detail(OrderType.PRODUCTION, 'test-1')
    assert (view.good_quantity, view.error_quantity, view.processed_quantity) == (None,None,None)
    assert not view.result_complete
    assert [unit.raw_status for unit in view.units] == [99,99]


def test_competing_reviews_allow_only_one_version_update(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    order_repository.require_review(stored.run.id, 'Testunterbrechung')
    version = order_repository.snapshot().orders[0].run.version
    requests = [ReviewRequest(request_id=uuid4(), expected_version=version, outcome=outcome) for outcome in ('completed','interrupted')]
    def save(request):
        """Gibt den fachlichen Konflikt zurück, statt einen Threadfehler zu verbergen."""
        try:
            return RunReviewService(order_repository).review(stored.run.id, request)
        except OrderConflict:
            return 'conflict'
    with ThreadPoolExecutor(max_workers=2) as executor:
        outcomes = list(executor.map(save, requests))
    assert outcomes.count('conflict') == 1
    assert order_repository.snapshot().orders[0].run.version == version + 1


def test_manual_review_never_resets_active_plc_and_blocks_next_kind(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    order_repository.admit(OrderType.DELIVERY, order_payload(2))
    order_repository.require_review(stored.run.id, 'Testunterbrechung')
    version = order_repository.snapshot().orders[0].run.version
    RunReviewService(order_repository).review(stored.run.id, ReviewRequest(request_id=uuid4(), expected_version=version, outcome='completed'))
    gateway = SimulatedGateway()
    gateway.snapshots[OrderType.PRODUCTION] = finished_snapshot(order_repository)
    service = OrderDispatchService(order_repository, gateway, SETTINGS, FakeLeadership())
    asyncio.run(service.tick(gateway.snapshots))
    assert gateway.events == []
    assert order_repository.snapshot().dispatch.active_run_id == stored.run.id
    gateway.snapshots[OrderType.PRODUCTION] = replace(gateway.snapshots[OrderType.PRODUCTION], command=0,status=0,product_count=0,products=())
    asyncio.run(service.tick(gateway.snapshots))
    assert order_repository.snapshot().dispatch.active_run_id is None
    asyncio.run(service.tick(gateway.snapshots))
    assert gateway.events == [('start',OrderType.DELIVERY,2)]


def test_recovery_finishes_partially_cleared_reset_without_losing_results(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    ProductResultService(order_repository, SETTINGS).observe(stored.run.id, finished_snapshot(order_repository))
    order_repository.transition(stored.run.id, RunPhase.AWAITING_RESET)
    gateway = SimulatedGateway(order_repository)
    gateway.snapshots[OrderType.PRODUCTION] = replace(finished_snapshot(order_repository), products=())
    OrderRecoveryService(order_repository).reconcile(order_repository.snapshot().orders[0],gateway.snapshots)
    service = OrderDispatchService(order_repository, gateway, SETTINGS, FakeLeadership())
    asyncio.run(service.tick(gateway.snapshots))
    asyncio.run(service.tick(gateway.snapshots))
    view = OrderQueryService(order_repository, SETTINGS).detail(OrderType.PRODUCTION,'test-1')
    assert (view.good_quantity,view.error_quantity) == (1,1)
    assert view.run_phase == RunPhase.COMPLETED
    assert gateway.events == [('ack',OrderType.PRODUCTION)]


def test_status_zero_with_nonzero_count_is_not_ready(order_repository, order_payload):
    order_repository.admit(OrderType.PRODUCTION,order_payload())
    gateway = SimulatedGateway()
    gateway.snapshots[OrderType.DELIVERY] = replace(gateway.snapshots[OrderType.DELIVERY],product_count=2)
    asyncio.run(OrderDispatchService(order_repository,gateway,SETTINGS,FakeLeadership()).tick(gateway.snapshots))
    assert gateway.events == []


def test_only_one_worker_leader_can_write_until_connection_released(order_engine):
    async def scenario():
        """Hält zwei unabhängige Führungssessions auf demselben Schema."""
        first, second = WorkerLeadership(order_engine), WorkerLeadership(order_engine)
        try:
            assert await first.acquire()
            assert await first.acquire()
            assert not await second.acquire()
            await first.close()
            assert await second.acquire()
            await second.assert_owned()
        finally:
            if first.connection is not None:
                await first.close()
            await second.close()
    asyncio.run(scenario())


def test_new_process_preserves_fifo_and_marks_uncertain_start_for_review(order_repository,order_payload):
    first = running_order(order_repository,order_payload(1))
    second = order_repository.admit(OrderType.DELIVERY,order_payload(2))
    with order_repository.engine.connect() as connection:
        schema = connection.execute(text('SELECT current_schema()')).scalar_one()
    source = '''
import json,sys
from sqlalchemy import create_engine
from app.repositories.order_repository import OrderRepository
from app.services.order_recovery_service import OrderRecoveryService
engine=create_engine(sys.argv[1],connect_args={"options":"-csearch_path="+sys.argv[2]})
repository=OrderRepository(engine)
snapshot=repository.snapshot()
active=next(item for item in snapshot.orders if item.run.id==snapshot.dispatch.active_run_id)
OrderRecoveryService(repository).reconcile(active,{})
print(json.dumps({"ids":[item.run.id for item in snapshot.orders],"sequences":[item.order.accepted_sequence for item in snapshot.orders],"review":repository.snapshot().orders[0].run.review_required}))
engine.dispose()
'''
    result = subprocess.run([sys.executable,'-c',source,order_repository.engine.url.render_as_string(hide_password=False),schema],check=True,capture_output=True,text=True,timeout=15)
    proof = json.loads(result.stdout)
    assert proof['ids'] == [first.run.id,second.run.id]
    assert proof['sequences'] == [1,2]
    assert proof['review']
    assert order_repository.reserve_next() is None


def test_later_plc_contradiction_preserves_facts_and_requires_new_review(order_repository,order_payload):
    """Manuelle Mengen dürfen neu belegte Einzelresultate nicht aus der DB verdrängen."""
    stored = running_order(order_repository,order_payload())
    order_repository.require_review(stored.run.id,'Testunterbrechung')
    version = order_repository.snapshot().orders[0].run.version
    RunReviewService(order_repository).review(stored.run.id,ReviewRequest(
        request_id=uuid4(),expected_version=version,outcome='completed',good_quantity=2,error_quantity=0,
    ))
    gateway = SimulatedGateway()
    gateway.snapshots[OrderType.PRODUCTION] = finished_snapshot(order_repository)
    asyncio.run(OrderDispatchService(order_repository,gateway,SETTINGS,FakeLeadership()).tick(gateway.snapshots))
    current = order_repository.snapshot().orders[0]
    assert [unit.result for unit in current.units] == ['good','failed']
    assert current.run.review_required
    assert current.run.manual_good_quantity == 2 and current.run.manual_error_quantity == 0
    assert gateway.events == []


def test_failed_result_commit_does_not_acknowledge_plc(order_repository,order_payload,monkeypatch):
    """Vor einem fehlgeschlagenen Resultatcommit gibt es keinen verlustreichen Reset."""
    from sqlalchemy.exc import OperationalError
    stored = running_order(order_repository,order_payload())
    gateway = SimulatedGateway()
    gateway.snapshots[OrderType.PRODUCTION] = finished_snapshot(order_repository)
    service = OrderDispatchService(order_repository,gateway,SETTINGS,FakeLeadership())
    def fail(*args):
        """Simuliert einen fehlgeschlagenen Persistenzzugriff."""
        raise OperationalError('Testausfall',{},None)
    monkeypatch.setattr(service.results,'observe',fail)
    with pytest.raises(OperationalError):
        asyncio.run(service.tick(gateway.snapshots))
    assert gateway.events == []
    assert order_repository.snapshot().dispatch.active_run_id == stored.run.id


@pytest.mark.parametrize('phase',[RunPhase.START_PENDING,RunPhase.RUNNING,RunPhase.AWAITING_RESET])
def test_execution_timeout_preserves_reservation_and_requires_review(order_repository,order_payload,phase):
    """Start-, Lauf- und Resettimeout dürfen weder freigeben noch einen Doppelstart erzeugen."""
    from datetime import timedelta
    stored = running_order(order_repository,order_payload())
    if phase == RunPhase.RUNNING:
        order_repository.transition(stored.run.id,phase)
    elif phase == RunPhase.AWAITING_RESET:
        ProductResultService(order_repository,SETTINGS).observe(stored.run.id,finished_snapshot(order_repository))
        order_repository.transition(stored.run.id,phase)
    instant = order_repository.clock()
    order_repository.clock = lambda: instant + timedelta(seconds=1000)
    gateway = SimulatedGateway()
    gateway.snapshots[OrderType.PRODUCTION] = replace(gateway.snapshots[OrderType.PRODUCTION],order_number=1,command=1,status=1 if phase==RunPhase.RUNNING else 0)
    asyncio.run(OrderDispatchService(order_repository,gateway,SETTINGS,FakeLeadership()).tick(gateway.snapshots))
    current = order_repository.snapshot()
    assert current.orders[0].run.review_required
    assert current.dispatch.active_run_id == stored.run.id
    assert gateway.events == []
