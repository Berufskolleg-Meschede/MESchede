"""Echter HTTP-Vertrag der Lagerbestands-Route ohne Anlagenzugriff."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.domain.lager_snapshot import GehaeuseBestand, LagerSnapshot, ProduktBestand
from app.routers.plc_storage_router import router


def client_for(gateway):
    application = FastAPI()
    application.state.plc_storage_gateway = gateway
    application.include_router(router)
    return TestClient(application)


def test_get_plc_storage_returns_snapshot_fields():
    gateway = AsyncMock()
    gateway.read.return_value = LagerSnapshot(
        gehaeuse=GehaeuseBestand(gesamt=10, rot=3, silber=4, schwarz=3),
        deckel_blau=12,
        deckel_gruen=8,
        produkte=ProduktBestand(
            gesamt=21, salz_rot=1, salz_silber=2, salz_schwarz=3,
            pfeffer_rot=4, pfeffer_silber=5, pfeffer_schwarz=6,
        ),
        observed_at=datetime(2026, 10, 14, 8, 0, tzinfo=timezone.utc),
    )
    client = client_for(gateway)

    response = client.get("/plc-storage/")

    assert response.status_code == 200
    body = response.json()
    assert body["gehaeuse"] == {"gesamt": 10, "rot": 3, "silber": 4, "schwarz": 3}
    assert body["deckel_blau"] == 12
    assert body["deckel_gruen"] == 8
    assert body["produkte"]["salz_rot"] == 1
    assert body["produkte"]["pfeffer_schwarz"] == 6
    assert body["observed_at"] == "2026-10-14T08:00:00+00:00"


def test_get_plc_storage_returns_503_and_reconnects_on_plc_error():
    gateway = AsyncMock()
    gateway.read.side_effect = KeyError("LagerGehaeuse")
    client = client_for(gateway)

    response = client.get("/plc-storage/")

    assert response.status_code == 503
    gateway.reconnect.assert_awaited_once()
