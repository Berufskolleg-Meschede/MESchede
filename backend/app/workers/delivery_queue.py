import asyncio
import logging
import os
from functools import partial
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, PrivateAttr, field_validator

from ..clients.opc_ua_client import OpcUaClient
from ..clients.execution import run_opc
from .order_execution import PlcSession, execute_order
from ..models.mes_auftrag import MESAuftrag
from ..services.settings_service import get_current_settings
from .diagnostics import WorkerDiagnostics
from ..services.analytics import (
    observe_run_completed,
    observe_run_error,
    observe_run_started,
)

logger = logging.getLogger(__name__)


class DeliveryOrderPayload(BaseModel):
    order_id: str = Field(min_length=1, max_length=128)
    mes_auftrag: MESAuftrag
    _analytics_run_id: int | None = PrivateAttr(default=None)

    @field_validator("order_id")
    @classmethod
    def strip_order_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("order_id darf nicht leer sein.")
        return normalized


delivery_queue: asyncio.Queue = asyncio.Queue()
_current_delivery: Optional[DeliveryOrderPayload] = None
_delivery_worker_task: Optional[asyncio.Task] = None
_diagnostics = WorkerDiagnostics()
_accepted_orders: dict[str, DeliveryOrderPayload] = {}


def get_accepted_order(order_id: str) -> Optional[DeliveryOrderPayload]:
    return _accepted_orders.get(order_id)


def accept_order(payload: DeliveryOrderPayload) -> bool:
    """Enqueue once per process; never silently replay an identical order ID."""
    existing = _accepted_orders.get(payload.order_id)
    if existing is not None:
        if existing.model_dump() != payload.model_dump():
            raise ValueError("order_id already used with a different payload")
        return False
    delivery_queue.put_nowait(payload)
    _accepted_orders[payload.order_id] = payload.model_copy(deep=True)
    return True


def get_delivery_queue_size() -> int:
    return delivery_queue.qsize()


def get_current_delivery_order_id() -> Optional[str]:
    return _current_delivery.order_id if _current_delivery else None


def get_worker_status() -> dict:
    return _diagnostics.snapshot(_delivery_worker_task, delivery_queue, get_current_delivery_order_id())


async def start_delivery_worker() -> None:
    global _delivery_worker_task
    if _delivery_worker_task and not _delivery_worker_task.done():
        return
    _diagnostics.phase = "starting"
    _delivery_worker_task = asyncio.create_task(_worker_loop(), name="delivery-worker")
    _delivery_worker_task.add_done_callback(
        lambda task: _diagnostics.task_finished(task, "Delivery", logger)
    )
    logger.info("Delivery worker started")


async def stop_delivery_worker() -> None:
    global _delivery_worker_task
    if not _delivery_worker_task:
        return
    _delivery_worker_task.cancel()
    try:
        await _delivery_worker_task
    except asyncio.CancelledError:
        pass
    _delivery_worker_task = None


async def _worker_loop() -> None:
    async def resolve_current_root(client):
        return await _get_root_node(client, get_current_settings().opcua_node_delivery_order)

    session = PlcSession(_create_client, resolve_current_root)
    try:
        while True:
            if session.client is None:
                try:
                    _diagnostics.phase = "connecting"
                    await session.connect()
                    logger.info("Delivery worker: order node resolved: %s", session.root)
                except Exception as error:
                    _diagnostics.last_error = f"{type(error).__name__}: {error}"
                    logger.exception("Failed to create OPC UA client (delivery)")
                    await session.close()
                    _diagnostics.phase = "retrying_connection"
                    await asyncio.sleep(2.0)
                    continue
            _diagnostics.phase = "waiting_for_order"
            order = await delivery_queue.get()
            global _current_delivery
            _current_delivery = order
            _diagnostics.last_order_id = order.order_id
            logger.info("Delivery order %s: dequeued; checking PLC readiness", order.order_id)
            try:
                node_name = get_current_settings().opcua_node_delivery_order
                _diagnostics.phase = "discovering_nodes"
                await session.select_order_root(partial(_get_root_node, node_name=node_name))
                await execute_order(
                    session, order, _send_order, _diagnostics, logger, "Delivery",
                    on_started=lambda observed_at: observe_run_started(order._analytics_run_id, observed_at),
                    on_completed=lambda observed_at: observe_run_completed(order._analytics_run_id, observed_at),
                )
                _diagnostics.last_completed_order_id = order.order_id
                _diagnostics.last_error = None
                logger.info("Delivery order %s completed; PLC reset confirmed", order.order_id)
            except asyncio.CancelledError:
                logger.info(
                    "Delivery order %s interrupted during %s", order.order_id, _diagnostics.phase
                )
                raise
            except Exception as error:
                _diagnostics.last_error = f"{type(error).__name__}: {error}"
                await asyncio.to_thread(
                    observe_run_error, order._analytics_run_id, type(error).__name__
                )
                logger.exception("Delivery order %s failed", order.order_id)
                await session.close()
            finally:
                session.get_root = resolve_current_root
                _current_delivery = None
                delivery_queue.task_done()
    except asyncio.CancelledError:
        raise
    finally:
        await session.close()


async def _create_client() -> OpcUaClient:
    load_dotenv()
    opc_ua_url = os.getenv("OPC_UA_URL")
    if not opc_ua_url:
        raise RuntimeError("OPC_UA_URL is not set")
    client = OpcUaClient(opc_ua_url)
    if await client.connect() is False:
        raise RuntimeError("Failed to connect to OPC UA server")
    return client


async def _get_root_node(opc_client: OpcUaClient, node_name: str):
    db_node = await opc_client.find_db_mes_schnittstelle()
    if db_node is None:
        raise KeyError("OPC UA node not found: 'DB_MES_Schnittstelle'")
    return await run_opc(opc_client._get_child, db_node, node_name)


async def _send_order(opc_client: OpcUaClient, root_node, order: DeliveryOrderPayload) -> None:
    settings = get_current_settings()
    await run_opc(
        opc_client.write_order, root_node, order.mes_auftrag, 4,
        settings.opcua_node_kopf, settings.opcua_node_inhalt,
        settings.opcua_node_auftragssteuerung, settings.opcua_node_produktqueue_pattern,
    )
