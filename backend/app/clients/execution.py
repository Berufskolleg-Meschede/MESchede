"""Keep cancelled OPC UA requests distinct from asyncio task cancellation."""

import asyncio
from concurrent.futures import CancelledError, TimeoutError as RequestTimeout

from opcua import ua


class OpcUaConnectionError(ConnectionError):
    pass


def _invoke(function, args):
    try:
        return function(*args)
    except (CancelledError, RequestTimeout, OSError,
            ua.uaerrors.BadSessionClosed, ua.uaerrors.BadSessionIdInvalid,
            ua.uaerrors.BadSecureChannelClosed, ua.uaerrors.BadConnectionClosed) as error:
        # Convert here, before asyncio converts concurrent CancelledError into
        # asyncio.CancelledError and incorrectly terminates the worker task.
        raise OpcUaConnectionError(f"OPC UA request interrupted: {type(error).__name__}: {error}") from error


async def run_opc(function, *args):
    return await asyncio.get_running_loop().run_in_executor(None, _invoke, function, args)
