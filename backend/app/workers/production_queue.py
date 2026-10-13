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


class ProductionOrderPayload(BaseModel):
    order_id: str
    mes_auftrag: MESAuftrag


order_queue: asyncio.Queue = asyncio.Queue()
_current_order: Optional[ProductionOrderPayload] = None
_worker_task: Optional[asyncio.Task] = None
_diagnostics = WorkerDiagnostics()


def get_queue_size() -> int:
    return order_queue.qsize()


def get_current_order_id() -> Optional[str]:
    return _current_order.order_id if _current_order else None


def get_worker_status() -> dict:
    return _diagnostics.snapshot(_worker_task, order_queue, get_current_order_id())


async def start_worker() -> None:
    global _worker_task
    if _worker_task and not _worker_task.done():
        return
    _diagnostics.phase = "starting"
    _worker_task = asyncio.create_task(_worker_loop(), name="production-worker")
    _worker_task.add_done_callback(
        lambda task: _diagnostics.task_finished(task, "Production", logger)
    )
    logger.info("Production worker started")


async def stop_worker() -> None:
    global _worker_task
    if not _worker_task:
        return
    _worker_task.cancel()
    try:
        await _worker_task
    except asyncio.CancelledError:
        pass
    _worker_task = None


async def _worker_loop() -> None:
    opc_client: Optional[OpcUaClient] = None
    try:
        while True:
            if opc_client is None:
                try:
                    _diagnostics.phase = "connecting"
                    opc_client = await _create_client()
                    logger.info("Production worker: connected to OPC UA server")
                except Exception as error:
                    _diagnostics.last_error = f"{type(error).__name__}: {error}"
                    logger.exception("Failed to create OPC UA client")
                    opc_client = None
                    _diagnostics.phase = "retrying_connection"
                    await asyncio.sleep(2.0)
                    continue
            _diagnostics.phase = "waiting_for_order"
            order = await order_queue.get()
            global _current_order
            _current_order = order
            _diagnostics.last_order_id = order.order_id
            logger.info("Production order %s: dequeued; checking PLC readiness", order.order_id)
            try:
                _diagnostics.phase = "discovering_nodes"
                node_name = get_current_settings().opcua_node_production_order
                root_node = await _get_root_node(opc_client, node_name)
                logger.info("Production order %s: order node resolved: %s", order.order_id, root_node)
                _diagnostics.phase = "waiting_for_plc_ready"
                await _wait_for_plc_ready(opc_client, root_node)
                _diagnostics.phase = "rest_buffer"
                await asyncio.sleep(3.0)
                logger.info(
                    "Production order %s: writing %s queue items and starting PLC",
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
                logger.info("Production order %s completed; PLC reset confirmed", order.order_id)
            except asyncio.CancelledError:
                logger.info(
                    "Production order %s interrupted during %s", order.order_id, _diagnostics.phase
                )
                raise
            except Exception as error:
                _diagnostics.last_error = f"{type(error).__name__}: {error}"
                logger.exception("Production order %s failed", order.order_id)
                try:
                    await opc_client.disconnect()
                except Exception:
                    logger.exception("Failed to disconnect after error")
                opc_client = None
            finally:
                _current_order = None
                order_queue.task_done()
    except asyncio.CancelledError:
        raise
    finally:
        if opc_client is not None:
            try:
                await opc_client.disconnect()
            except Exception:
                logger.exception("Failed to disconnect during shutdown")


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


async def _send_order(opc_client: OpcUaClient, root_node, order: ProductionOrderPayload) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, opc_client.write_order, root_node, order.mes_auftrag, 1)
