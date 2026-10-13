"""Shared, phase-aware order execution: reconnect reads, never replay starts."""

import asyncio
import logging

from ..clients.execution import OpcUaConnectionError
from . import plc_handshake

logger = logging.getLogger(__name__)
RECONNECT_DELAY_S = 0.5
REST_BUFFER_S = 3.0


class PlcSession:
    def __init__(self, create_client, get_root):
        self.create_client = create_client
        self.get_root = get_root
        self.client = None
        self.root = None

    async def connect(self):
        self.client = await self.create_client()
        self.root = await self.get_root(self.client)

    async def close(self):
        client, self.client = self.client, None
        self.root = None
        if client is not None:
            try:
                await client.disconnect()
            except Exception:
                logger.exception("OPC UA disconnect failed during recovery")

    async def wait(self, operation, timeout_s, diagnostics, phase):
        deadline = asyncio.get_running_loop().time() + timeout_s
        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TimeoutError(f"PLC {phase} timeout, including connection recovery")
            if self.client is None:
                diagnostics.phase = "reconnecting"
                try:
                    await self.connect()
                except Exception as error:
                    diagnostics.last_error = f"{type(error).__name__}: {error}"
                    await self.close()
                    await asyncio.sleep(RECONNECT_DELAY_S)
                    continue
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TimeoutError(f"PLC {phase} timeout, including connection recovery")
            diagnostics.phase = phase
            try:
                return await operation(self.client, self.root, remaining)
            except OpcUaConnectionError as error:
                diagnostics.last_error = str(error)
                logger.warning("PLC connection lost during %s; reconnecting without replaying the order", phase)
                await self.close()
                await asyncio.sleep(RECONNECT_DELAY_S)


async def execute_order(session, order, send_order, diagnostics, worker_logger, kind):
    await session.wait(plc_handshake.wait_for_plc_ready, 600.0, diagnostics, "waiting_for_plc_ready")
    diagnostics.phase = "rest_buffer"
    await asyncio.sleep(REST_BUFFER_S)
    diagnostics.phase = "writing_order"
    worker_logger.info("%s order %s: writing %s queue items and starting PLC",
                       kind, order.order_id, len(order.mes_auftrag.inhalt.Produktqueue))
    try:
        await send_order(session.client, session.root, order)
    except OpcUaConnectionError as error:
        # The write may have reached the PLC before the response was lost.
        # Observe feedback after reconnect, but NEVER send start again.
        diagnostics.last_error = str(error)
        worker_logger.warning("Order %s: write outcome uncertain; observing PLC feedback, not resending", order.order_id)
        await session.close()
    await session.wait(plc_handshake.wait_for_plc_started, 30.0, diagnostics, "waiting_for_plc_started")
    await session.wait(plc_handshake.wait_for_plc_finished, 600.0, diagnostics, "waiting_for_completion")
    # Only status 5 permits acknowledgement. If a reset response is lost,
    # readiness accepts an already applied reset instead of awaiting 5 again.
    await session.wait(plc_handshake.wait_for_plc_ready, 30.0, diagnostics, "waiting_for_reset")
