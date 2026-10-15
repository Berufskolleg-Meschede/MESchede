"""HTTP-Grenze zur Auftragsdomäne mit verständlichen, stabilen Fehlerantworten."""

import asyncio

from fastapi import HTTPException, Request
from opcua import ua
from sqlalchemy.exc import SQLAlchemyError

from app.domain.order_run import OrderConflict, OrderType
from app.models.order_dto import OrderPayload
from app.models.order_input import OrderInputError
from app.services.order_admission_service import OrderAdmissionService
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
    except OrderInputError as error:
        raise HTTPException(422, [{"loc": ["body", *error.path], "msg": str(error), "type": "value_error"}]) from error
    except LookupError as error:
        raise HTTPException(404, str(error)) from error
    except ValueError as error:
        raise HTTPException(422, str(error)) from error
    except SQLAlchemyError as error:
        raise HTTPException(503, "Die Auftragsdaten sind derzeit nicht erreichbar. Bitte erneut versuchen.") from error


async def admit_order(worker: OrderWorkerHost, kind: OrderType, payload: OrderPayload) -> dict:
    """Löst Wiederholungen ohne PLC-Zugriff auf und validiert nur erstmalige Annahmen."""
    if not worker.running:
        raise HTTPException(503, "Der Auftragsworker ist nicht gestartet. Bitte den Backendstatus prüfen.")
    existing = await execute_order_operation(lambda: worker.repository.order_detail(kind, payload.order_id))
    validate = None
    if existing is None:
        try:
            snapshot = await worker.input_service.catalog(kind)
        except (OSError, TimeoutError, KeyError, ValueError, ua.UaError) as error:
            raise HTTPException(503, "Produktkatalog oder Queue-Kapazität nicht verfügbar. Bitte die Produktdaten prüfen.") from error
        except SQLAlchemyError as error:
            raise HTTPException(503, "Der Produktkatalog ist derzeit nicht lesbar. Bitte die Datenbank prüfen.") from error
        validate = lambda candidate: worker.input_service.validate(candidate, snapshot)
    admission = OrderAdmissionService(worker.repository)
    return await execute_order_operation(lambda: admission.accept(kind, payload, validate))
