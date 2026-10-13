import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from ..clients.opc_ua_client import OpcUaClient
from ..models.mes_auftrag import MESAuftrag
from ..services.settings_service import get_current_settings
from .diagnostics import WorkerDiagnostics
from .plc_handshake import (
    wait_for_plc_ready as _wait_for_plc_ready,
    wait_for_plc_started as _wait_for_plc_started,
    wait_for_plc_done as _wait_for_plc_done,
)

logger = logging.getLogger(__name__)


class DeliveryOrderPayload(BaseModel):
    order_id: str
    mes_auftrag: MESAuftrag


delivery_queue: asyncio.Queue = asyncio.Queue()
_current_delivery: Optional[DeliveryOrderPayload] = None
_delivery_worker_task: Optional[asyncio.Task] = None
_diagnostics = WorkerDiagnostics()


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
    opc_client: Optional[OpcUaClient] = None
    try:
        while True:
            if opc_client is None:
                try:
                    _diagnostics.phase = "connecting"
                    opc_client = await _create_client()
                    logger.info("Delivery worker: connected to OPC UA server")
                except Exception as error:
                    _diagnostics.last_error = f"{type(error).__name__}: {error}"
                    logger.exception("Failed to create OPC UA client (delivery)")
                    opc_client = None
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
                _diagnostics.phase = "discovering_nodes"
                node_name = get_current_settings().opcua_node_delivery_order
                root_node = await _get_root_node(opc_client, node_name)
                logger.info("Delivery order %s: order node resolved: %s", order.order_id, root_node)
                _diagnostics.phase = "waiting_for_plc_ready"
                await _wait_for_plc_ready(opc_client, root_node)
                _diagnostics.phase = "rest_buffer"
                await asyncio.sleep(3.0)
                logger.info(
                    "Delivery order %s: writing %s queue items and starting PLC",
                    order.order_id, len(order.mes_auftrag.inhalt.Produktqueue),
                )
                _diagnostics.phase = "writing_order"
                await _send_order(opc_client, root_node, order)
                _diagnostics.phase = "waiting_for_plc_started"
                await _wait_for_plc_started(opc_client, root_node)
                _diagnostics.phase = "waiting_for_completion_and_reset"
                await _wait_for_plc_done(opc_client, root_node)
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
                logger.exception("Delivery order %s failed", order.order_id)
                try:
                    await opc_client.disconnect()
                except Exception:
                    logger.exception("Failed to disconnect after delivery error")
                opc_client = None
            finally:
                _current_delivery = None
                delivery_queue.task_done()
    except asyncio.CancelledError:
        raise
    finally:
        if opc_client is not None:
            try:
                await opc_client.disconnect()
            except Exception:
                logger.exception("Failed to disconnect delivery worker during shutdown")


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
    loop = asyncio.get_running_loop()
    db_node = await opc_client.find_db_mes_schnittstelle()
    if db_node is None:
        raise KeyError("OPC UA node not found: 'DB_MES_Schnittstelle'")
    return await loop.run_in_executor(None, opc_client._get_child, db_node, node_name)


async def _send_order(opc_client: OpcUaClient, root_node, order: DeliveryOrderPayload) -> None:
    settings = get_current_settings()
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(
        None, opc_client.write_order, root_node, order.mes_auftrag, 4,
        settings.opcua_node_kopf, settings.opcua_node_inhalt,
        settings.opcua_node_auftragssteuerung, settings.opcua_node_produktqueue_pattern,
    )
