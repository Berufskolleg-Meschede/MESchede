"""Prüft belegbare Laufübergänge und den mengenbasierten Reviewvertrag."""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.domain.order_run import InvalidTransition, OrderRun, RunPhase
from app.models.order_dto import ReviewRequest


def test_accepted_order_cannot_be_reported_completed_without_feedback():
    run = OrderRun(RunPhase.QUEUED)
    with pytest.raises(InvalidTransition):
        run.transition_to(RunPhase.COMPLETED)
    assert run.status == "pending"


def test_fast_completion_is_accepted_without_observing_running_between_polls():
    run = OrderRun(RunPhase.START_PENDING)
    run.transition_to(RunPhase.COMPLETION_OBSERVED)
    assert run.status == "completed"
    assert run.phase != RunPhase.COMPLETED


def test_uncertain_run_requires_review_instead_of_success():
    run = OrderRun(RunPhase.RUNNING)
    run.transition_to(RunPhase.REVIEW_REQUIRED)
    assert run.status == "review_required"


def test_review_accepts_unknown_quantities_without_explanation():
    review = ReviewRequest(request_id=uuid4(), expected_version=1, outcome="completed")
    assert review.good_quantity is None
    assert review.error_quantity is None


@pytest.mark.parametrize("quantity", [-1, 1.5, True, "2"])
def test_review_rejects_non_integer_or_negative_quantities(quantity):
    with pytest.raises(ValidationError):
        ReviewRequest(
            request_id=uuid4(), expected_version=1, outcome="completed", good_quantity=quantity,
        )
