import logging

from fastapi import APIRouter, HTTPException, Request
from opcua import ua

router = APIRouter(prefix="/plc-storage", tags=["plc-storage"])

logger = logging.getLogger(__name__)


@router.get("/")
async def get_plc_storage(request: Request):
    gateway = request.app.state.plc_storage_gateway
    try:
        snapshot = await gateway.read()
    except (OSError, TimeoutError, KeyError, ValueError, ua.UaError) as error:
        logger.warning("SPS-Lagerbestand konnte nicht gelesen werden: %s", error)
        try:
            await gateway.reconnect()
        except (OSError, ua.UaError):
            logger.warning("Die PLC-Verbindung konnte nicht sauber getrennt werden.")
        raise HTTPException(status_code=503, detail=str(error))
    return {
        "gehaeuse": {
            "gesamt": snapshot.gehaeuse.gesamt,
            "rot": snapshot.gehaeuse.rot,
            "silber": snapshot.gehaeuse.silber,
            "schwarz": snapshot.gehaeuse.schwarz,
        },
        "deckel_blau": snapshot.deckel_blau,
        "deckel_gruen": snapshot.deckel_gruen,
        "produkte": {
            "gesamt": snapshot.produkte.gesamt,
            "salz_rot": snapshot.produkte.salz_rot,
            "salz_silber": snapshot.produkte.salz_silber,
            "salz_schwarz": snapshot.produkte.salz_schwarz,
            "pfeffer_rot": snapshot.produkte.pfeffer_rot,
            "pfeffer_silber": snapshot.produkte.pfeffer_silber,
            "pfeffer_schwarz": snapshot.produkte.pfeffer_schwarz,
        },
        "observed_at": snapshot.observed_at.isoformat(),
    }
