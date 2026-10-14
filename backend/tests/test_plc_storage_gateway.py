"""Konsistentes Lesen der vier SPS-Lagerknoten ohne Schreibzugriff."""

import asyncio
from unittest.mock import MagicMock

import pytest

from app.clients.plc_storage_gateway import PlcStorageGateway
from app.models.settings import Settings
from tests.test_opc_ua_client import _make_client, _make_mock_node


def _make_lager_tree(lager_gehaeuse="LagerGehaeuse", deckel_1="MagazinDeckel_1",
                      deckel_2="MagazinDeckel_2", lager_produkte="LagerProdukte"):
    gehaeuse = _make_mock_node(lager_gehaeuse)
    gehaeuse.get_children.return_value = [
        _make_mock_node("StueckzahlGesamt", value=10),
        _make_mock_node("StueckzahlRot", value=3),
        _make_mock_node("StueckzahlSilber", value=4),
        _make_mock_node("StueckzahlSchwarz", value=3),
    ]
    deckel1 = _make_mock_node(deckel_1)
    deckel1.get_children.return_value = [_make_mock_node("Stueckzahl", value=12)]
    deckel2 = _make_mock_node(deckel_2)
    deckel2.get_children.return_value = [_make_mock_node("Stueckzahl", value=8)]
    produkte = _make_mock_node(lager_produkte)
    produkte.get_children.return_value = [
        _make_mock_node("StueckzahlGesamt", value=21),
        _make_mock_node("StueckzahlSalzRot", value=1),
        _make_mock_node("StueckzahlSalzSilber", value=2),
        _make_mock_node("StueckzahlSalzSchwarz", value=3),
        _make_mock_node("StueckzahlPfefferRot", value=4),
        _make_mock_node("StueckzahlPfefferSilber", value=5),
        _make_mock_node("StueckzahlPfefferSchwarz", value=6),
    ]
    database = MagicMock()
    database.get_children.return_value = [gehaeuse, deckel1, deckel2, produkte]
    return database


@pytest.fixture
def gateway_tree():
    gateway = PlcStorageGateway("unused-test-url")
    client = _make_client()
    database = _make_lager_tree()
    gateway.client = client
    gateway.database = database
    try:
        yield gateway
    finally:
        asyncio.run(gateway.close())


def test_read_builds_snapshot_from_configured_nodes(gateway_tree):
    snapshot = asyncio.run(gateway_tree.read())

    assert snapshot.gehaeuse.gesamt == 10
    assert snapshot.gehaeuse.rot == 3
    assert snapshot.gehaeuse.silber == 4
    assert snapshot.gehaeuse.schwarz == 3
    assert snapshot.deckel_blau == 12
    assert snapshot.deckel_gruen == 8
    assert snapshot.produkte.gesamt == 21
    assert snapshot.produkte.salz_rot == 1
    assert snapshot.produkte.salz_silber == 2
    assert snapshot.produkte.salz_schwarz == 3
    assert snapshot.produkte.pfeffer_rot == 4
    assert snapshot.produkte.pfeffer_silber == 5
    assert snapshot.produkte.pfeffer_schwarz == 6


def test_read_resolves_configured_node_names():
    configured = Settings(
        opcua_node_lager_gehaeuse="CustomGehaeuse",
        opcua_node_magazin_deckel_1="CustomDeckel1",
        opcua_node_magazin_deckel_2="CustomDeckel2",
        opcua_node_lager_produkte="CustomProdukte",
    )
    gateway = PlcStorageGateway("unused-test-url", settings_provider=lambda: configured)
    gateway.client = _make_client()
    gateway.database = _make_lager_tree(
        lager_gehaeuse="CustomGehaeuse", deckel_1="CustomDeckel1",
        deckel_2="CustomDeckel2", lager_produkte="CustomProdukte",
    )

    snapshot = asyncio.run(gateway.read())

    assert snapshot.deckel_blau == 12
    assert snapshot.produkte.gesamt == 21
    asyncio.run(gateway.close())


def test_missing_node_raises_key_error(gateway_tree):
    gateway_tree.database.get_children.return_value = []

    with pytest.raises(KeyError, match="LagerGehaeuse"):
        asyncio.run(gateway_tree.read())
