"""HTTP-Grenze zur Auftragsdomäne mit verständlichen, stabilen Fehlerantworten."""

import asyncio

from fastapi import HTTPException, Request
from sqlalchemy.exc import SQLAlchemyError

from app.domain.order_run import OrderConflict
from app.workers.order_worker_host import OrderWorkerHost


def get_order_worker(request: Request) -> OrderWorkerHost:
    """Bezieht den gemeinsamen Worker aus dem Lifecycle der konkreten Anwendung."""
    worker = getattr(request.app.state, "order_worker", None)
    if worker is None:
        raise HTTPException(503, "Die Auftragsverwaltung ist noch nicht gestartet.")
    return worker


async def execute_order_operation(operation):
    """Führt synchronen DB-Zugriff außerhalb des Eventloops mit fachlicher Fehlerzuordnung aus."""
    try:
        return await asyncio.to_thread(operation)
    except OrderConflict as error:
        raise HTTPException(409, str(error)) from error
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(503, "Die Auftragsdaten sind derzeit nicht erreichbar. Bitte erneut versuchen.") from error
