"""Fachliche Nachweise für echte Resultate, manuelle Mengen und Wiederaufnahme."""

from datetime import timedelta
from uuid import uuid4

import pytest

from app.domain.order_run import OrderConflict, OrderType, RunPhase
from app.domain.plc_snapshot import PlcSnapshot, ProductObservation
from app.models.order_dto import ReviewRequest
from app.services.order_query_service import OrderQueryService
from app.services.order_recovery_service import OrderRecoveryService
from app.services.product_result_service import ProductResultService
from app.services.run_review_service import RunReviewService
from app.settings import OrderSettings


def running_order(repository, payload):
    """Stellt einen nachweisbar zur PLC-Übergabe vorbereiteten Testlauf her."""
    stored = repository.admit(OrderType.PRODUCTION, payload)
    repository.reserve_next()
    repository.transition(stored.run.id, RunPhase.START_PENDING)
    return stored


def finished_snapshot(repository, number=1, statuses=(11, 12)):
    """Verwendet absichtlich synthetische Codes, keine behaupteten realen PLC-Codes."""
    return PlcSnapshot(
        OrderType.PRODUCTION, number, 1, 5, repository.clock(),
        tuple(ProductObservation(index, 1, index + 10, index + 1, status, 7 if status == 12 else 0)
              for index, status in enumerate(statuses)),
    )


def test_repeated_product_results_do_not_increment_quantities(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    settings = OrderSettings(contract_verified=True, product_results={11: "good", 12: "failed"})
    service = ProductResultService(order_repository, settings)
    observation = finished_snapshot(order_repository)
    service.observe(stored.run.id, observation)
    original = OrderQueryService(order_repository, settings).detail(OrderType.PRODUCTION, "test-1")
    service.observe(stored.run.id, observation)
    current = OrderQueryService(order_repository, settings).detail(OrderType.PRODUCTION, "test-1")
    assert (current.good_quantity, current.error_quantity, current.processed_quantity) == (1, 1, 2)
    assert current.version == original.version
    assert current.result_complete


def test_unverified_codes_do_not_fabricate_good_or_failed_quantities(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    settings = OrderSettings()
    ProductResultService(order_repository, settings).observe(stored.run.id, finished_snapshot(order_repository))
    view = OrderQueryService(order_repository, settings).detail(OrderType.PRODUCTION, "test-1")
    assert view.good_quantity is None and view.error_quantity is None
    assert view.status == "completed"
    assert not view.result_complete


def test_foreign_order_does_not_change_product_results(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    service = ProductResultService(order_repository, OrderSettings(contract_verified=True, product_results={11: "good"}))
    with pytest.raises(OrderConflict):
        service.observe(stored.run.id, finished_snapshot(order_repository, number=99))
    assert all(unit.result is None for unit in order_repository.snapshot().orders[0].units)


def test_idle_after_unconfirmed_start_requires_review(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    snapshots = {kind: PlcSnapshot(kind, 1, 0, 0, order_repository.clock()) for kind in OrderType}
    current = order_repository.snapshot().orders[0]
    OrderRecoveryService(order_repository).reconcile(current, snapshots)
    assert order_repository.snapshot().orders[0].run.review_required
    assert order_repository.reserve_next() is None


def test_active_correlated_run_is_preserved_on_recovery(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    observation = PlcSnapshot(OrderType.PRODUCTION, 1, 1, 1, order_repository.clock())
    OrderRecoveryService(order_repository).reconcile(order_repository.snapshot().orders[0], {OrderType.PRODUCTION: observation})
    assert not order_repository.snapshot().orders[0].run.review_required
    assert order_repository.snapshot().dispatch.active_run_id == stored.run.id


def test_manual_review_without_note_keeps_unknown_quantities_unknown(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    order_repository.require_review(stored.run.id, "Start nicht nachweisbar")
    before = order_repository.snapshot().orders[0]
    request = ReviewRequest(request_id=uuid4(), expected_version=before.run.version, outcome="completed")
    review = RunReviewService(order_repository).review(stored.run.id, request)
    assert review.outcome == "completed"
    view = OrderQueryService(order_repository, OrderSettings()).detail(OrderType.PRODUCTION, "test-1")
    assert view.has_manual_review
    assert view.good_quantity is None and view.processed_quantity is None
    assert order_repository.snapshot().dispatch.active_run_id == stored.run.id


def test_repeated_review_does_not_change_version_or_count_twice(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    order_repository.require_review(stored.run.id, "Unterbrochen")
    request = ReviewRequest(request_id=uuid4(), expected_version=order_repository.snapshot().orders[0].run.version,
                            outcome="completed", good_quantity=1, error_quantity=1)
    service = RunReviewService(order_repository)
    first = service.review(stored.run.id, request)
    version = order_repository.snapshot().orders[0].run.version
    assert service.review(stored.run.id, request) == first
    assert order_repository.snapshot().orders[0].run.version == version
    view = OrderQueryService(order_repository, OrderSettings()).detail(OrderType.PRODUCTION, "test-1")
    assert view.processed_quantity == 2
    assert view.quantity_source == "manual"
    assert all(unit.result is None for unit in order_repository.snapshot().orders[0].units)


def test_review_rejects_total_above_plan_and_stale_version(order_repository, order_payload):
    stored = running_order(order_repository, order_payload())
    order_repository.require_review(stored.run.id, "Unterbrochen")
    version = order_repository.snapshot().orders[0].run.version
    service = RunReviewService(order_repository)
    with pytest.raises(ValueError):
        service.review(stored.run.id, ReviewRequest(request_id=uuid4(), expected_version=version,
                        outcome="completed", good_quantity=2, error_quantity=1))
    service.review(stored.run.id, ReviewRequest(request_id=uuid4(), expected_version=version, outcome="unknown"))
    with pytest.raises(OrderConflict):
        service.review(stored.run.id, ReviewRequest(request_id=uuid4(), expected_version=version, outcome="completed"))


def test_missing_and_stale_sources_are_not_reported_as_fresh(order_repository):
    query = OrderQueryService(order_repository, OrderSettings())
    assert query.overview(True).sources[OrderType.PRODUCTION].freshness == "unknown"
    order_repository.source_success(OrderType.PRODUCTION, order_repository.clock() - timedelta(seconds=11))
    assert query.overview(True).sources[OrderType.PRODUCTION].freshness == "stale"
