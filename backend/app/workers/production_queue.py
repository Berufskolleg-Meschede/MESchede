import asyncio
import logging
import os
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from ..clients.opc_ua_client import OpcUaClient

logger = logging.getLogger(__name__)


class ProductionOrderPayload(BaseModel):
    order_id: str
    payload: Dict[str, Any] = Field(default_factory=dict)


order_queue: asyncio.Queue = asyncio.Queue()
_current_order: Optional[ProductionOrderPayload] = None
_worker_task: Optional[asyncio.Task] = None


def get_queue_size() -> int:
    return order_queue.qsize()


def get_current_order_id() -> Optional[str]:
    if _current_order is None:
        return None
    return _current_order.order_id


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
    try:
        while True:
            if opc_client is None:
                try:
                    opc_client = await _create_client()
                except Exception:
                    logger.exception("Failed to create OPC UA client")
                    await asyncio.sleep(2.0)
                    continue
            order = await order_queue.get()
            global _current_order
            _current_order = order
            try:
                await _wait_for_plc_ready(opc_client)
                await _send_order(opc_client, order)
                await _wait_for_plc_done(opc_client)
                logger.info("Order processed", extra={"order_id": order.order_id})
            except Exception as exc:
                logger.exception("Order processing failed", extra={"order_id": order.order_id})
                try:
                    await opc_client.disconnect()
                except Exception:
                    logger.exception("Failed to disconnect OPC UA client after error")
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
                logger.exception("Failed to disconnect OPC UA client during shutdown")


async def _create_client() -> OpcUaClient:
    load_dotenv()
    opc_ua_url = os.getenv("OPC_UA_URL")
    if not opc_ua_url:
        raise RuntimeError("OPC_UA_URL is not set")
    client = OpcUaClient(opc_ua_url)
    connected = await client.connect()
    if connected is False:
        raise RuntimeError("Failed to connect to OPC UA server")
    return client


async def _wait_for_plc_ready(opc_client: OpcUaClient, timeout_s: float = 30.0) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    while True:
        ready = True
        if ready:
            return
        if loop.time() - start >= timeout_s:
            raise TimeoutError("PLC not ready within timeout")
        await asyncio.sleep(0.5)


async def _send_order(opc_client: OpcUaClient, order: ProductionOrderPayload) -> None:
    _ = opc_client
    _ = order
    # TODO: write order payload to the correct OPC UA nodes.


async def _wait_for_plc_done(opc_client: OpcUaClient, timeout_s: float = 600.0) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    while True:
        done = True
        if done:
            return
        if loop.time() - start >= timeout_s:
            raise TimeoutError("PLC did not finish within timeout")
        await asyncio.sleep(0.5)
