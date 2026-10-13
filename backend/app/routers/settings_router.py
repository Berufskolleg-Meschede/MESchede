from fastapi import APIRouter, HTTPException, status
from ..models.settings import Settings, SettingsBase
from ..services import settings_service
from ..workers import delivery_queue, production_queue

router = APIRouter(prefix="/settings", tags=["settings"])


def _field_error(field: str, message: str) -> list[dict]:
    return [{"loc": ["body", field], "msg": message, "type": "value_error"}]


@router.get("/", response_model=Settings)
async def get_settings():
    return settings_service.get_current_settings()


@router.put("/", response_model=Settings)
async def put_settings(
    payload: SettingsBase,
):
    current = settings_service.get_current_settings()

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

    updated = Settings(
        opcua_node_production_order=payload.opcua_node_production_order,
        opcua_node_delivery_order=payload.opcua_node_delivery_order,
        polling_interval_ms=payload.polling_interval_ms,
    )

    settings_service.apply_settings(updated)

    return settings_service.get_current_settings()
