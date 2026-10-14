"""MES command/PLC feedback handshake shared by production and delivery."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable

from ..clients.opc_ua_client import OpcUaClient
from ..clients.execution import run_opc

logger = logging.getLogger(__name__)
POLL_INTERVAL_S = 0.5


def _log_completion(root_node, phase: str) -> None:
    logger.info(
        "PLC completion detected (%s): StatusMES=5; phase=%s; "
        "starting reset of Produktqueue, Anzahl and Auftragssteuerung_MES",
        root_node, phase,
    )


async def wait_for_plc_ready(
    opc_client: OpcUaClient, root_node, timeout_s: float = 600.0, acknowledgement=None
) -> None:
    acknowledgement = acknowledgement or CompletedOrderAcknowledgement()
    if acknowledgement.queue_attempted:
        # Completion was seen before a reset request lost its response.
        return await acknowledgement(opc_client, root_node, timeout_s)
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    previous_state = None
    logger.info("PLC ready check (%s): reading MES feedback and command", root_node)
    while True:
        status = await run_opc(opc_client.read_status_mes, root_node)
        command = await run_opc(opc_client.read_auftragssteuerung, root_node)
        state = (status, command)
        if state != previous_state:
            logger.info(
                "PLC ready check (%s): StatusMES=%s, Auftragssteuerung_MES=%s",
                root_node, status, command,
            )
            previous_state = state
        if status == 0 and command == 0:
            return
        if status == 5 and command == 1:
            # Recover a finished order left latched across a backend restart.
            # Feedback 5 is the PLC's permission to acknowledge completion.
            _log_completion(root_node, "ready/recovery")
            await acknowledgement(
                opc_client, root_node, max(0, deadline - loop.time())
            )
            return
        if loop.time() >= deadline:
            raise TimeoutError(
                "PLC not ready: expected feedback StatusMES=0 and "
                f"Auftragssteuerung_MES=0, got status={status}, command={command}"
            )
        await asyncio.sleep(POLL_INTERVAL_S)


async def _wait_for_status(
    opc_client: OpcUaClient,
    root_node,
    expected: tuple[int, ...],
    timeout_s: float,
    phase: str,
) -> int:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    previous_status = None
    while True:
        status = await run_opc(opc_client.read_status_mes, root_node)
        if status != previous_status:
            logger.info("PLC %s (%s): StatusMES=%s", phase, root_node, status)
            previous_status = status
        if status in expected:
            if status == 5:
                _log_completion(root_node, phase)
            return status
        if loop.time() >= deadline:
            raise TimeoutError(
                f"PLC {phase} timeout: expected feedback StatusMES in {expected}, got {status}"
            )
        await asyncio.sleep(POLL_INTERVAL_S)


async def wait_for_plc_started(
    opc_client: OpcUaClient, root_node, timeout_s: float = 30.0
) -> int:
    # A short order may already be finished before the first poll sees status 1.
    return await _wait_for_status(opc_client, root_node, (1, 5), timeout_s, "start")


async def wait_for_plc_done(
    opc_client: OpcUaClient,
    root_node,
    timeout_s: float = 600.0,
    reset_timeout_s: float = 30.0,
    on_completion: Callable[[datetime], None] | None = None,
) -> datetime:
    # Status 0 immediately after a start command is not completion. Only the
    # PLC's feedback 5 authorizes acknowledging the finished order.
    await wait_for_plc_finished(opc_client, root_node, timeout_s)
    completed_at = datetime.now(timezone.utc)
    if on_completion is not None:
        await asyncio.get_running_loop().run_in_executor(None, on_completion, completed_at)
    await CompletedOrderAcknowledgement()(opc_client, root_node, reset_timeout_s)
    return completed_at


async def wait_for_plc_finished(opc_client, root_node, timeout_s=600.0):
    return await _wait_for_status(opc_client, root_node, (5,), timeout_s, "completion")


async def wait_for_plc_idle(opc_client, root_node, timeout_s=30.0):
    """Only confirm reset; never require or acknowledge completion again."""
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    while True:
        status = await run_opc(opc_client.read_status_mes, root_node)
        command = await run_opc(opc_client.read_auftragssteuerung, root_node)
        count = await run_opc(opc_client.read_anzahl, root_node)
        if status == command == count == 0:
            return
        if loop.time() >= deadline:
            raise TimeoutError(
                f"PLC reset timeout: expected StatusMES=0, Auftragssteuerung_MES=0, Anzahl=0; "
                f"got status={status}, command={command}, count={count}"
            )
        await asyncio.sleep(POLL_INTERVAL_S)


class CompletedOrderAcknowledgement:
    """Retain observed completion and reset progress across reconnects."""

    def __init__(self):
        self.queue_attempted = False
        self.queue_cleared = False
        self.count_attempted = False
        self.count_cleared = False
        self.command_attempted = False
        self.command_cleared = False

    async def __call__(self, opc_client, root_node, timeout_s):
        deadline = asyncio.get_running_loop().time() + timeout_s
        # The caller already observed feedback 5. Do not read it again before
        # acknowledging: a transient 5 is still the observed completion event.
        if not self.queue_cleared:
            self.queue_attempted = True
            await run_opc(opc_client.clear_product_queue, root_node)
            self.queue_cleared = True
        if not self.count_cleared:
            if self.count_attempted:
                self.count_cleared = await run_opc(opc_client.read_anzahl, root_node) == 0
            if not self.count_cleared:
                self.count_attempted = True
                await run_opc(opc_client.write_anzahl, root_node, 0)
                self.count_cleared = True
        if not self.command_cleared:
            if self.command_attempted:
                self.command_cleared = await run_opc(opc_client.read_auftragssteuerung, root_node) == 0
            if not self.command_cleared:
                self.command_attempted = True
                await run_opc(opc_client.write_auftragssteuerung, root_node, 0)
                self.command_cleared = True
        logger.info("PLC reset (%s): Produktqueue cleared, Anzahl=0, Auftragssteuerung_MES=0; awaiting idle feedback", root_node)
        await wait_for_plc_idle(
            opc_client, root_node, max(0, deadline - asyncio.get_running_loop().time())
        )
