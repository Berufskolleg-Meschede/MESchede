from datetime import date, time
from unittest.mock import MagicMock
import pytest

from opcua import ua
from app.clients.opc_ua_client import OpcUaClient
from app.models.mes_auftrag import MESAuftrag, AuftragKopf, AuftragInhalt, ProduktDaten


def _make_mock_node(browse_name: str, value=0, vtype=ua.VariantType.Byte):
    node = MagicMock()
    bn = MagicMock()
    bn.Name = browse_name
    node.get_browse_name.return_value = bn
    dv = MagicMock()
    dv.Value.VariantType = vtype
    node.get_data_value.return_value = dv
    node.get_value.return_value = value
    node.get_children.return_value = []
    return node


def _make_client() -> OpcUaClient:
    client = OpcUaClient.__new__(OpcUaClient)
    client.client = MagicMock()
    return client


# --- _get_child ---

def test_get_child_found():
    client = _make_client()
    child_a = _make_mock_node("Alpha")
    child_b = _make_mock_node("Beta")
    parent = MagicMock()
    parent.get_children.return_value = [child_a, child_b]

    result = client._get_child(parent, "Beta")
    assert result is child_b


def test_get_child_missing_raises():
    client = _make_client()
    parent = MagicMock()
    parent.get_children.return_value = [_make_mock_node("Alpha")]

    with pytest.raises(KeyError, match="Missing"):
        client._get_child(parent, "Missing")


# --- read_auftragssteuerung ---

def test_read_auftragssteuerung_returns_value():
    client = _make_client()
    steuerung = _make_mock_node("Auftragssteuerung", value=1)
    kopf = _make_mock_node("Kopf")
    kopf.get_children.return_value = [steuerung]
    root = MagicMock()
    root.get_children.return_value = [kopf]

    assert client.read_auftragssteuerung(root) == 1


# --- write_order ---

def test_write_order_sets_auftragssteuerung_to_1():
    client = _make_client()

    kopf_children = [
        _make_mock_node(n) for n in [
            "Auftragsnummer", "Kundennummer", "Startdatum", "Startzeit",
            "AuftragsArt", "Priorität", "Parameter", "Auftragssteuerung",
        ]
    ]

    produkt0_children = [
        _make_mock_node(n) for n in ["ProduktID", "Produkttext", "Seriennummer", "Sequenznummer", "Takt"]
    ]
    produkt0 = _make_mock_node("Produktqueue[0]")
    produkt0.get_children.return_value = produkt0_children

    inhalt_children = [
        _make_mock_node("ProduktID"),
        _make_mock_node("Anzahl"),
        _make_mock_node("SeriennummerStart"),
        produkt0,
    ]

    kopf = _make_mock_node("Kopf")
    kopf.get_children.return_value = kopf_children
    inhalt = _make_mock_node("Inhalt")
    inhalt.get_children.return_value = inhalt_children
    root = MagicMock()
    root.get_children.return_value = [kopf, inhalt]

    order = MESAuftrag(
        kopf=AuftragKopf(
            Auftragsnummer=1,
            Startdatum=date(2026, 6, 23),
            Startzeit=time(8, 0),
        ),
        inhalt=AuftragInhalt(
            Produktqueue=[ProduktDaten(ProduktID=42)],
        ),
    )

    client.write_order(root, order, auftragsart=1)

    anzahl_node = next(
        n for n in inhalt_children if n.get_browse_name().Name == "Anzahl"
    )
    anzahl_node.set_data_value.assert_called_once()
    assert anzahl_node.set_data_value.call_args[0][0].Value.Value == 1

    auftragssteuerung_node = next(
        n for n in kopf_children if n.get_browse_name().Name == "Auftragssteuerung"
    )
    auftragssteuerung_node.set_data_value.assert_called_once()
    written_variant = auftragssteuerung_node.set_data_value.call_args[0][0].Value
    assert written_variant.Value == 1
