"""Consume and persist inventory events from the configured RabbitMQ queue."""

import json
import logging
import os
import threading
from datetime import datetime, timezone

import pika
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.article import Article
from app.models.storage import Storage, StorageEvent

logger = logging.getLogger(__name__)
_MAX_DATABASE_INTEGER = 2_147_483_647
_stop_event = threading.Event()
_status_lock = threading.Lock()
_worker_thread: threading.Thread | None = None
_connection: pika.BlockingConnection | None = None
_status = {
    "configured": False,
    "connected": False,
    "last_error": None,
    "last_message_at": None,
}


def get_storage_consumer_status() -> dict:
    """Return a thread-safe snapshot of RabbitMQ consumer health."""
    with _status_lock:
        return dict(_status)


def _set_status(**values: object) -> None:
    with _status_lock:
        _status.update(values)


def _parse_event(body: bytes, broker_message_id: str | None) -> dict:
    """Validate the proposed inventory event envelope before persistence."""
    payload = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("Die RabbitMQ-Nachricht muss ein JSON-Objekt sein.")

    event_id = payload.get("event_id") or broker_message_id
    if not isinstance(event_id, str) or not event_id.strip() or len(event_id) > 128:
        raise ValueError("Die RabbitMQ-Nachricht benötigt eine eindeutige event_id.")

    event_type = payload.get("event_type")
    if event_type not in ("snapshot", "delta"):
        raise ValueError("event_type muss 'snapshot' oder 'delta' sein.")

    product_id = payload.get("product_id")
    if type(product_id) is not int or product_id <= 0 or product_id > _MAX_DATABASE_INTEGER:
        raise ValueError("product_id muss eine positive Ganzzahl sein.")

    raw_time = payload.get("occurred_at")
    if not isinstance(raw_time, str):
        raise ValueError("occurred_at muss einen ISO-8601-Zeitpunkt enthalten.")
    occurred_at = datetime.fromisoformat(raw_time.replace("Z", "+00:00"))
    if occurred_at.tzinfo is None:
        raise ValueError("occurred_at muss eine Zeitzone enthalten.")
    occurred_at = occurred_at.astimezone(timezone.utc).replace(tzinfo=None)

    quantity = payload.get("quantity")
    quantity_delta = payload.get("quantity_delta")
    if event_type == "snapshot":
        if type(quantity) is not int or quantity < 0 or quantity > _MAX_DATABASE_INTEGER:
            raise ValueError("Ein Snapshot benötigt eine nicht negative quantity.")
        if quantity_delta is not None:
            raise ValueError("Ein Snapshot darf quantity_delta nicht enthalten.")
    else:
        if (
            type(quantity_delta) is not int
            or quantity_delta == 0
            or abs(quantity_delta) > _MAX_DATABASE_INTEGER
        ):
            raise ValueError("Eine Änderung benötigt eine von null verschiedene quantity_delta.")
        if quantity is not None:
            raise ValueError("Eine Änderung darf quantity nicht enthalten.")

    return {
        "event_id": event_id.strip(),
        "event_type": event_type,
        "product_id": product_id,
        "occurred_at": occurred_at,
        "quantity": quantity,
        "quantity_delta": quantity_delta,
    }


def _persist_event(event: dict, session_factory=None) -> bool:
    """Apply one idempotent inventory event; return false for a duplicate."""
    if session_factory is None:
        from app.db.session import SessionLocal

        session_factory = SessionLocal

    with session_factory() as session:
        existing_event = session.get(StorageEvent, event["event_id"])
        if existing_event is not None:
            return False

        article = session.get(Article, event["product_id"])
        if article is None:
            raise ValueError(f"Unbekannte product_id {event['product_id']}.")

        stock = session.execute(
            select(Storage)
            .where(Storage.article_id == event["product_id"])
            .with_for_update()
        ).scalars().all()
        if len(stock) > 1:
            raise ValueError(
                f"Für product_id {event['product_id']} existiert mehr als ein Lagerdatensatz."
            )
        stock = stock[0] if stock else None
        if stock is None:
            stock = Storage(article_id=event["product_id"], quantity=None)

        if stock.updated_at is not None and event["occurred_at"] < stock.updated_at:
            session.add(StorageEvent(
                event_id=event["event_id"],
                article_id=event["product_id"],
                event_type=event["event_type"],
                occurred_at=event["occurred_at"],
            ))
            session.add(stock)
            session.commit()
            return True

        if event["event_type"] == "snapshot":
            stock.quantity = event["quantity"]
        elif stock.quantity is None:
            raise ValueError("Eine Änderung kann ohne vorherigen Snapshot nicht angewendet werden.")
        else:
            updated_quantity = stock.quantity + event["quantity_delta"]
            if updated_quantity < 0 or updated_quantity > _MAX_DATABASE_INTEGER:
                raise ValueError("Die Änderung würde einen ungültigen Bestand erzeugen.")
            stock.quantity = updated_quantity

        stock.updated_at = event["occurred_at"]
        session.add(stock)
        session.add(StorageEvent(
            event_id=event["event_id"],
            article_id=event["product_id"],
            event_type=event["event_type"],
            occurred_at=event["occurred_at"],
        ))
        try:
            session.commit()
        except IntegrityError:
            session.rollback()
            if session.get(StorageEvent, event["event_id"]) is not None:
                return False
            raise
        return True


def _on_message(channel, method, properties, body: bytes) -> None:
    """Validate and persist a delivered message before acknowledging it."""
    try:
        event = _parse_event(body, properties.message_id)
        _persist_event(event)
    except (ValueError, TypeError, json.JSONDecodeError) as error:
        logger.warning("RabbitMQ-Lagerereignis verworfen: %s", error)
        channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        return

    _set_status(last_message_at=datetime.now(timezone.utc).isoformat(), last_error=None)
    channel.basic_ack(delivery_tag=method.delivery_tag)


def _consume_loop() -> None:
    """Reconnect to the configured inbound queue until application shutdown."""
    global _connection
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    queue_name = os.getenv("RABBITMQ_STORAGE_INBOUND_QUEUE")
    if not rabbitmq_url or not queue_name or queue_name == "storage":
        _set_status(configured=False, connected=False)
        logger.warning(
            "RabbitMQ-Lagerconsumer deaktiviert: RABBITMQ_URL und eine separate "
            "RABBITMQ_STORAGE_INBOUND_QUEUE werden benötigt."
        )
        return

    _set_status(configured=True)
    while not _stop_event.is_set():
        try:
            _connection = pika.BlockingConnection(pika.URLParameters(rabbitmq_url))
            channel = _connection.channel()
            channel.queue_declare(queue=queue_name, passive=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue=queue_name, on_message_callback=_on_message)
            _set_status(connected=True, last_error=None)
            channel.start_consuming()
        except Exception as error:
            _set_status(connected=False, last_error=f"Verbindung fehlgeschlagen ({type(error).__name__}).")
            if not _stop_event.is_set():
                logger.warning(
                    "RabbitMQ-Lagerconsumer getrennt (%s); erneuter Versuch folgt.",
                    type(error).__name__,
                )
                _stop_event.wait(5)
        finally:
            _set_status(connected=False)
            if _connection is not None and _connection.is_open:
                _connection.close()
            _connection = None


def start_storage_consumer() -> None:
    """Start the inventory consumer when a distinct inbound queue is configured."""
    global _worker_thread
    if _worker_thread is not None and _worker_thread.is_alive():
        return
    _stop_event.clear()
    _worker_thread = threading.Thread(
        target=_consume_loop,
        name="storage-rabbitmq-consumer",
        daemon=True,
    )
    _worker_thread.start()


def stop_storage_consumer() -> None:
    """Stop the consumer and close its active RabbitMQ connection."""
    global _worker_thread, _connection
    _stop_event.set()
    active_connection = _connection
    if active_connection is not None and active_connection.is_open:
        active_connection.add_callback_threadsafe(active_connection.close)
    if _worker_thread is not None:
        _worker_thread.join(timeout=10)
    _worker_thread = None
    _set_status(connected=False)
