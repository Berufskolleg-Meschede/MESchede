import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from ..clients.opc_ua_client import OpcUaClient
from ..models.mes_auftrag import MESAuftrag

logger = logging.getLogger(__name__)


class ProductionOrderPayload(BaseModel):
    order_id: str
    mes_auftrag: MESAuftrag


order_queue: asyncio.Queue = asyncio.Queue()
_current_order: Optional[ProductionOrderPayload] = None
_worker_task: Optional[asyncio.Task] = None


def get_queue_size() -> int:
    return order_queue.qsize()


def get_current_order_id() -> Optional[str]:
    return _current_order.order_id if _current_order else None


async def start_worker() -> None:
    global _worker_task
    if _worker_task and not _worker_task.done():
        return
    _worker_task = asyncio.create_task(_worker_loop())


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
    root_node = None
    try:
        while True:
            if opc_client is None:
                try:
                    opc_client = await _create_client()
                    root_node = await _get_root_node(opc_client)
                except Exception:
                    logger.exception("Failed to create OPC UA client")
                    await asyncio.sleep(2.0)
                    continue
            order = await order_queue.get()
            global _current_order
            _current_order = order
            try:
                await _wait_for_plc_ready(opc_client, root_node)
                await asyncio.sleep(3.0)
                await _send_order(opc_client, root_node, order)
                await _wait_for_plc_done(opc_client, root_node)
                logger.info("Order processed", extra={"order_id": order.order_id})
            except Exception:
                logger.exception("Order processing failed", extra={"order_id": order.order_id})
                try:
                    await opc_client.disconnect()
                except Exception:
                    logger.exception("Failed to disconnect after error")
                opc_client = None
                root_node = None
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


async def _get_root_node(opc_client: OpcUaClient):
    loop = asyncio.get_running_loop()
    db_node = await opc_client.find_db_mes_schnittstelle()
    return await loop.run_in_executor(None, opc_client._get_child, db_node, "MESAuftragProduktion")


async def _wait_for_plc_ready(opc_client: OpcUaClient, root_node, timeout_s: float = 30.0) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    while True:
        value = await loop.run_in_executor(None, opc_client.read_auftragssteuerung, root_node)
        if value == 0:
            return
        if loop.time() - start >= timeout_s:
            raise TimeoutError("PLC not ready within timeout")
        await asyncio.sleep(0.5)


async def _send_order(opc_client: OpcUaClient, root_node, order: ProductionOrderPayload) -> None:
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, opc_client.write_order, root_node, order.mes_auftrag, 1)


async def _wait_for_plc_done(opc_client: OpcUaClient, root_node, timeout_s: float = 600.0) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    while True:
        value = await loop.run_in_executor(None, opc_client.read_auftragssteuerung, root_node)
        if value == 0:
            return
        if loop.time() - start >= timeout_s:
            raise TimeoutError("PLC did not finish within timeout")
        await asyncio.sleep(0.5)
