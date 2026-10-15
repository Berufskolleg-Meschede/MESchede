"""Publishes durable stock deltas to the ERP-facing RabbitMQ queue."""

from datetime import datetime, timezone

from sqlalchemy import Engine
from sqlmodel import Session, select

from app.clients.rabbitmq.base import send_storage_message
from app.models.storage_outbox_event import StorageOutboxEvent


_BATCH_SIZE = 100


def publish_pending_storage_events(engine: Engine) -> int:
    """Publishes pending events and marks them sent only after broker confirmation."""
    published_count = 0
    with Session(engine, expire_on_commit=False) as session:
        with session.begin():
            events = session.exec(
                select(StorageOutboxEvent)
                .where(StorageOutboxEvent.published_at.is_(None))
                .order_by(StorageOutboxEvent.created_at, StorageOutboxEvent.event_id)
                .limit(_BATCH_SIZE)
                .with_for_update(skip_locked=True)
            ).all()
            for event in events:
                send_storage_message(
                    event.product_id,
                    event.quantity_delta,
                    message_id=event.event_id,
                )
                event.published_at = datetime.now(timezone.utc)
                published_count += 1
    return published_count
