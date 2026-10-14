"""Nachweise für PostgreSQL-Persistenz, Annahmeidentität und globale FIFO-Reservierung."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from app.domain.order_run import OrderConflict, OrderType, RunPhase
from app.repositories.order_repository import OrderRepository


def test_duplicate_acceptance_returns_same_run_after_repository_restart(order_repository, order_payload):
    original = order_repository.admit(OrderType.PRODUCTION, order_payload())
    restarted = OrderRepository(order_repository.engine)
    duplicate = restarted.admit(OrderType.PRODUCTION, order_payload())
    assert duplicate.order.id == original.order.id
    assert duplicate.run.id == original.run.id
    assert len(restarted.snapshot().orders) == 1


def test_changed_payload_is_rejected_without_another_order(order_repository, order_payload):
    order_repository.admit(OrderType.PRODUCTION, order_payload())
    with pytest.raises(OrderConflict):
        order_repository.admit(OrderType.PRODUCTION, order_payload(quantity=3))
    assert len(order_repository.snapshot().orders) == 1


def test_equal_business_ids_in_different_types_do_not_collide(order_repository, order_payload):
    first = order_repository.admit(OrderType.PRODUCTION, order_payload(order_id="same"))
    second = order_repository.admit(OrderType.DELIVERY, order_payload(order_id="same"))
    assert first.run.id != second.run.id


def test_oldest_delivery_precedes_new_production_regardless_of_priority(order_repository, order_payload):
    first = order_repository.admit(OrderType.DELIVERY, order_payload(1))
    production = order_payload(2)
    production.mes_auftrag.kopf.Prioritaet = 2
    order_repository.admit(OrderType.PRODUCTION, production)
    chosen = order_repository.reserve_next()
    assert chosen.run.id == first.run.id
    assert chosen.run.phase == RunPhase.PREPARING.value


def test_concurrent_dispatchers_reserve_only_one_run(order_repository, order_payload):
    order_repository.admit(OrderType.PRODUCTION, order_payload(1))
    order_repository.admit(OrderType.DELIVERY, order_payload(2))
    with ThreadPoolExecutor(max_workers=2) as executor:
        reservations = list(executor.map(lambda _: order_repository.reserve_next(), range(2)))
    assert sum(reservation is not None for reservation in reservations) == 1


def test_concurrent_identical_acceptances_persist_one_order(order_repository, order_payload):
    with ThreadPoolExecutor(max_workers=2) as executor:
        orders = list(executor.map(
            lambda _: order_repository.admit(OrderType.PRODUCTION, order_payload()), range(2),
        ))
    assert orders[0].run.id == orders[1].run.id
    assert len(order_repository.snapshot().orders) == 1


def test_uncertain_production_blocks_delivery_after_restart(order_repository, order_payload):
    original = order_repository.admit(OrderType.PRODUCTION, order_payload(1))
    order_repository.admit(OrderType.DELIVERY, order_payload(2))
    order_repository.reserve_next()
    order_repository.require_review(original.run.id, "Start nicht nachweisbar")
    restarted = OrderRepository(order_repository.engine)
    assert restarted.reserve_next() is None
    assert restarted.snapshot().dispatch.active_run_id == original.run.id
    assert restarted.snapshot().orders[0].run.review_required


def test_source_failure_preserves_last_successful_observation(order_repository):
    instant = order_repository.clock()
    order_repository.source_success(OrderType.PRODUCTION, instant)
    order_repository.source_failure(OrderType.PRODUCTION, "Verbindung verloren")
    source = next(item for item in order_repository.snapshot().sources if item.order_type == "production")
    assert source.last_success_at == instant
    assert source.connection_status == "disconnected"
