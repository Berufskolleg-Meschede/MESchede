from __future__ import annotations
import json
import os
from pathlib import Path
import pika
from dotenv import load_dotenv

_BACKEND_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(dotenv_path=_BACKEND_ROOT / ".env")


class RabbitMQClient:
    def __init__(self, queue_name: str = "storage", url: str | None = None) -> None:
        self.queue_name = queue_name
        self.url = url or os.getenv("RABBITMQ_URL")
        if not self.url:
            raise RuntimeError("RABBITMQ_URL is not configured in .env")

        self._connection: pika.BlockingConnection | None = None
        self._channel: pika.adapters.blocking_connection.BlockingChannel | None = None

    def _connect(self) -> None:
        """Establish connection and channel if not already connected."""
        if self._connection is None or self._connection.is_closed:
            self._connection = pika.BlockingConnection(pika.URLParameters(self.url))
            self._channel = None

        if self._channel is None or self._channel.is_closed:
            self._channel = self._connection.channel()
            self._channel.queue_declare(queue=self.queue_name, durable=True)

    def publish_storage_message(self, product_id: int, quantity_delta: int) -> None:
        payload = {
            "product_id": product_id,
            "quantity_delta": quantity_delta,
        }
        self._connect()
        self._channel.basic_publish(
            exchange="",
            routing_key=self.queue_name,
            body=json.dumps(payload),
            properties=pika.BasicProperties(delivery_mode=2),
        )

    def close(self) -> None:
        """Close the connection explicitly."""
        if self._connection and self._connection.is_open:
            self._connection.close()
        self._connection = None
        self._channel = None

    def __enter__(self) -> RabbitMQClient:
        self._connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def send_storage_message(product_id: int, quantity_delta: int) -> None:
    """
    Send a storage change event to RabbitMQ.

    :param product_id: The article ID
    :param quantity_delta: The quantity change (positive for adding, negative for removing)
    """
    RabbitMQClient().publish_storage_message(product_id, quantity_delta)