import asyncio
import logging
import os
from functools import partial
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from ..clients.opc_ua_client import OpcUaClient
from ..clients.execution import run_opc
from .order_execution import PlcSession, execute_order
from ..models.mes_auftrag import MESAuftrag
from ..services.settings_service import get_current_settings
from .diagnostics import WorkerDiagnostics

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
    async def resolve_current_root(client):
        return await _get_root_node(client, get_current_settings().opcua_node_production_order)

    session = PlcSession(_create_client, resolve_current_root)
    try:
        while True:
            if session.client is None:
                try:
                    _diagnostics.phase = "connecting"
                    await session.connect()
                    logger.info("Production worker: order node resolved: %s", session.root)
                except Exception as error:
                    _diagnostics.last_error = f"{type(error).__name__}: {error}"
                    logger.exception("Failed to create OPC UA client (production)")
                    await session.close()
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
                node_name = get_current_settings().opcua_node_production_order
                _diagnostics.phase = "discovering_nodes"
                await session.select_order_root(partial(_get_root_node, node_name=node_name))
                await execute_order(session, order, _send_order, _diagnostics, logger, "Production")
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
                await session.close()
            finally:
                session.get_root = resolve_current_root
                _current_order = None
                order_queue.task_done()
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


async def _send_order(opc_client: OpcUaClient, root_node, order: ProductionOrderPayload) -> None:
    await run_opc(opc_client.write_order, root_node, order.mes_auftrag, 1)
