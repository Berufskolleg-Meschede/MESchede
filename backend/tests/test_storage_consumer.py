import json
from datetime import timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import pytest

from app.models.article import Article
from app.models.storage import Storage
from app.workers.storage_consumer import _parse_event, _persist_event


@pytest.fixture
def inventory_session_factory():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    with session_factory() as session:
        session.add(Article(id=17, name="Stahlträger", description="Testartikel", price=1.0))
        session.commit()
    yield session_factory
    engine.dispose()


def test_snapshot_persists_stock_and_duplicate_is_ignored(inventory_session_factory):
    event = _parse_event(
        json.dumps({
            "event_id": "snapshot-1",
            "event_type": "snapshot",
            "product_id": 17,
            "quantity": 12,
            "occurred_at": "2026-10-13T08:00:00Z",
        }).encode(),
        None,
    )

    assert _persist_event(event, inventory_session_factory) is True
    assert _persist_event(event, inventory_session_factory) is False

    with inventory_session_factory() as session:
        stock = session.query(Storage).filter_by(article_id=17).one()
        assert stock.quantity == 12


def test_delta_without_snapshot_does_not_assume_zero(inventory_session_factory):
    event = _parse_event(
        json.dumps({
            "event_id": "delta-1",
            "event_type": "delta",
            "product_id": 17,
            "quantity_delta": 3,
            "occurred_at": "2026-10-13T08:00:00Z",
        }).encode(),
        None,
    )

    with pytest.raises(ValueError, match="vorherigen Snapshot"):
        _persist_event(event, inventory_session_factory)


def test_invalid_delta_is_rejected():
    payload = {
        "event_id": "delta-1",
        "event_type": "delta",
        "product_id": 17,
        "quantity_delta": 0,
        "occurred_at": "2026-10-13T08:00:00Z",
    }

    with pytest.raises(ValueError, match="quantity_delta"):
        _parse_event(json.dumps(payload).encode(), None)


def test_message_id_can_supply_missing_event_id():
    event = _parse_event(
        json.dumps({
            "event_type": "snapshot",
            "product_id": 17,
            "quantity": 12,
            "occurred_at": "2026-10-13T08:00:00Z",
        }).encode(),
        "broker-event-1",
    )

    assert event["event_id"] == "broker-event-1"
    assert event["occurred_at"].tzinfo == timezone.utc
