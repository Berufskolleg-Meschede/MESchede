"""MES command/PLC feedback handshake shared by production and delivery."""

import asyncio
import logging

from ..clients.opc_ua_client import OpcUaClient
from ..services.settings_service import get_current_settings

logger = logging.getLogger(__name__)
POLL_INTERVAL_S = 0.5


async def wait_for_plc_ready(
    opc_client: OpcUaClient, root_node, timeout_s: float = 30.0
) -> None:
    settings = get_current_settings()
    kopf_node = settings.opcua_node_kopf
    feedback_node = settings.opcua_node_feedback
    auftragssteuerung_node = settings.opcua_node_auftragssteuerung
    status_node = settings.opcua_node_status
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    previous_state = None
    logger.info("PLC ready check (%s): reading MES feedback and command", root_node)
    while True:
        status = await loop.run_in_executor(None, opc_client.read_status_mes, root_node, feedback_node, status_node)
        command = await loop.run_in_executor(
            None, opc_client.read_auftragssteuerung, root_node, kopf_node, auftragssteuerung_node
        )
        state = (status, command)
        if state != previous_state:
            logger.info(
                "PLC ready check (%s): %s=%s, %s=%s",
                root_node, status_node, status, auftragssteuerung_node, command,
            )
            previous_state = state
        if status == 0 and command == 0:
            return
        if status == 5 and command == 1:
            # Recover a finished order left latched across a backend restart.
            # Feedback 5 is the PLC's permission to acknowledge completion.
            await loop.run_in_executor(
                None, opc_client.write_auftragssteuerung, root_node, 0, kopf_node, auftragssteuerung_node
            )
            logger.info("PLC ready check (%s): acknowledging a finished order", root_node)
        if loop.time() >= deadline:
            raise TimeoutError(
                f"PLC not ready: expected feedback {status_node}=0 and "
                f"{auftragssteuerung_node}=0, got status={status}, command={command}"
            )
        await asyncio.sleep(POLL_INTERVAL_S)


async def _wait_for_status(
    opc_client: OpcUaClient,
    root_node,
    expected: tuple[int, ...],
    timeout_s: float,
    phase: str,
    feedback_node: str,
    status_node: str,
) -> None:
    loop = asyncio.get_running_loop()
    deadline = loop.time() + timeout_s
    previous_status = None
    while True:
        status = await loop.run_in_executor(None, opc_client.read_status_mes, root_node, feedback_node, status_node)
        if status != previous_status:
            logger.info("PLC %s (%s): %s=%s", phase, root_node, status_node, status)
            previous_status = status
        if status in expected:
            return
        if loop.time() >= deadline:
            raise TimeoutError(
                f"PLC {phase} timeout: expected feedback {status_node} in {expected}, got {status}"
            )
        await asyncio.sleep(POLL_INTERVAL_S)


async def wait_for_plc_started(
    opc_client: OpcUaClient, root_node, timeout_s: float = 30.0
) -> None:
    settings = get_current_settings()
    # A short order may already be finished before the first poll sees status 1.
    await _wait_for_status(
        opc_client, root_node, (1, 5), timeout_s, "start",
        settings.opcua_node_feedback, settings.opcua_node_status,
    )


async def wait_for_plc_done(
    opc_client: OpcUaClient,
    root_node,
    timeout_s: float = 600.0,
    reset_timeout_s: float = 30.0,
) -> None:
    settings = get_current_settings()
    kopf_node = settings.opcua_node_kopf
    auftragssteuerung_node = settings.opcua_node_auftragssteuerung
    # Status 0 immediately after a start command is not completion. Only the
    # PLC's feedback 5 authorizes acknowledging the finished order.
    await _wait_for_status(
        opc_client, root_node, (5,), timeout_s, "completion",
        settings.opcua_node_feedback, settings.opcua_node_status,
    )
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, opc_client.write_auftragssteuerung, root_node, 0, kopf_node, auftragssteuerung_node)
    logger.info("PLC reset (%s): %s=0; awaiting idle feedback", root_node, auftragssteuerung_node)
    await wait_for_plc_ready(opc_client, root_node, reset_timeout_s)
