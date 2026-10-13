"""MES command/PLC feedback handshake shared by production and delivery."""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Callable

from ..clients.opc_ua_client import OpcUaClient

logger = logging.getLogger(__name__)
POLL_INTERVAL_S = 0.5


async def wait_for_plc_ready(
    opc_client: OpcUaClient, root_node, timeout_s: float = 30.0
) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    previous_state = None
    logger.info("PLC ready check (%s): reading MES feedback and command", root_node)
    while True:
        status = await loop.run_in_executor(None, opc_client.read_status_mes, root_node)
        command = await loop.run_in_executor(None, opc_client.read_auftragssteuerung, root_node)
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
            await loop.run_in_executor(None, opc_client.write_auftragssteuerung, root_node, 0)
            logger.info("PLC ready check (%s): acknowledging a finished order", root_node)
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
) -> tuple[int, datetime]:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    previous_status = None
    while True:
        status = await loop.run_in_executor(None, opc_client.read_status_mes, root_node)
        if status != previous_status:
            logger.info("PLC %s (%s): StatusMES=%s", phase, root_node, status)
            previous_status = status
        if status in expected:
            return status, datetime.now(timezone.utc)
        if loop.time() >= deadline:
            raise TimeoutError(
                f"PLC {phase} timeout: expected feedback StatusMES in {expected}, got {status}"
            )
        await asyncio.sleep(POLL_INTERVAL_S)


async def wait_for_plc_started(
    opc_client: OpcUaClient, root_node, timeout_s: float = 30.0
) -> tuple[int, datetime]:
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
    _, completion_observed_at = await _wait_for_status(
        opc_client, root_node, (5,), timeout_s, "completion"
    )
    loop = asyncio.get_running_loop()
    if on_completion is not None:
        await loop.run_in_executor(None, on_completion, completion_observed_at)
    await loop.run_in_executor(None, opc_client.write_auftragssteuerung, root_node, 0)
    logger.info("PLC reset (%s): Auftragssteuerung_MES=0; awaiting idle feedback", root_node)
    await wait_for_plc_ready(opc_client, root_node, reset_timeout_s)
    return completion_observed_at
