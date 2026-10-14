from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.db import get_session
from ..models.settings import Settings, SettingsBase
from ..services import settings_service
from ..workers import delivery_queue, production_queue

router = APIRouter(prefix="/settings", tags=["settings"])


def _field_error(field: str, message: str) -> list[dict]:
    return [{"loc": ["body", field], "msg": message, "type": "value_error"}]


@router.get("/", response_model=Settings)
async def get_settings(session: AsyncSession = Depends(get_session)):
    return await settings_service.load_settings(session)


@router.put("/", response_model=Settings)
async def put_settings(
    payload: SettingsBase,
    session: AsyncSession = Depends(get_session),
):
    current = await settings_service.load_settings(session)

    if (
        payload.opcua_node_production_order != current.opcua_node_production_order
        and production_queue.get_current_order_id() is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_field_error(
                "opcua_node_production_order",
                "Zielnode kann nicht geändert werden, während ein Produktionsauftrag "
                "aktiv ist. Bitte erneut versuchen, sobald der Auftrag abgeschlossen ist.",
            ),
        )

    if (
        payload.opcua_node_delivery_order != current.opcua_node_delivery_order
        and delivery_queue.get_current_delivery_order_id() is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=_field_error(
                "opcua_node_delivery_order",
                "Zielnode kann nicht geändert werden, während ein Lieferauftrag "
                "aktiv ist. Bitte erneut versuchen, sobald der Auftrag abgeschlossen ist.",
            ),
        )

    current.opcua_node_production_order = payload.opcua_node_production_order
    current.opcua_node_delivery_order = payload.opcua_node_delivery_order
    current.polling_interval_ms = payload.polling_interval_ms
    current.opcua_node_kopf = payload.opcua_node_kopf
    current.opcua_node_inhalt = payload.opcua_node_inhalt
    current.opcua_node_feedback = payload.opcua_node_feedback
    current.opcua_node_auftragssteuerung = payload.opcua_node_auftragssteuerung
    current.opcua_node_status = payload.opcua_node_status
    current.opcua_node_produktqueue_pattern = payload.opcua_node_produktqueue_pattern
    current.opcua_node_lager_gehaeuse = payload.opcua_node_lager_gehaeuse
    current.opcua_node_magazin_deckel_1 = payload.opcua_node_magazin_deckel_1
    current.opcua_node_magazin_deckel_2 = payload.opcua_node_magazin_deckel_2
    current.opcua_node_lager_produkte = payload.opcua_node_lager_produkte

    session.add(current)
    await session.commit()
    await session.refresh(current)

    settings_service.apply_settings(current)
    production_queue.update_poll_interval(current.polling_interval_ms / 1000)

    return current
