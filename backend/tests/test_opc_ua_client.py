import asyncio
from datetime import date, time, datetime, timezone
from unittest.mock import MagicMock
import pytest

from opcua import ua
from opcua.ua.ua_binary import variant_to_binary
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


# --- node discovery ---

def _discovery_node(name, identifier, namespace=2, display_name=None):
    node = _make_mock_node(name)
    node.nodeid = ua.NodeId(identifier, namespace)
    node.get_browse_name.return_value = ua.QualifiedName(name, namespace)
    node.get_display_name.return_value = ua.LocalizedText(display_name or name)
    node.get_children_descriptions.return_value = []
    return node


def _references(*nodes):
    references = []
    for node in nodes:
        reference = ua.ReferenceDescription()
        reference.NodeId = node.nodeid
        reference.BrowseName = node.get_browse_name.return_value
        reference.DisplayName = node.get_display_name.return_value
        references.append(reference)
    return references


def test_discovery_uses_objects_and_finds_db_before_browsing_deeper_branches():
    client = _make_client()
    objects = _discovery_node("Objects", 85, namespace=0)
    unrelated = _discovery_node("Server", 1)
    deeper = _discovery_node("ServerConfiguration", 2)
    plc = _discovery_node("PLC", 3)
    target = _discovery_node("DB_MES_Schnittstelle", 4, display_name="MES data")
    objects.get_children_descriptions.return_value = _references(unrelated, plc)
    unrelated.get_children_descriptions.return_value = _references(deeper)
    plc.get_children_descriptions.return_value = _references(target)
    nodes = {node.nodeid.to_string(): node for node in [objects, unrelated, deeper, plc, target]}
    client.client.get_objects_node.return_value = objects
    client.client.get_node.side_effect = lambda node_id: nodes[node_id.to_string()]

    assert asyncio.run(client.find_db_mes_schnittstelle()) is target

    client.client.get_root_node.assert_not_called()
    deeper.get_children_descriptions.assert_not_called()
    target.get_children_descriptions.assert_not_called()
    target.get_browse_name.assert_not_called()  # name is taken from the Browse response
    target.get_display_name.assert_not_called()


def test_discovery_terminates_on_cycles_and_shared_nodes():
    client = _make_client()
    root = _discovery_node("Objects", 85, namespace=0)
    first = _discovery_node("First", 1)
    second = _discovery_node("Second", 2)
    root.get_children_descriptions.return_value = _references(first, second)
    first.get_children_descriptions.return_value = _references(root, second)
    second.get_children_descriptions.return_value = _references(first)
    nodes = {node.nodeid.to_string(): node for node in [root, first, second]}
    client.client.get_node.side_effect = lambda node_id: nodes[node_id.to_string()]

    assert client._find_node_by_name_sync(root, "Missing", None) is None

    for node in nodes.values():
        node.get_children_descriptions.assert_called_once()


def test_discovery_respects_requested_namespace():
    client = _make_client()
    root = _discovery_node("Objects", 85, namespace=0)
    wrong_namespace = _discovery_node("DB_MES_Schnittstelle", 1, namespace=2)
    target = _discovery_node("DB_MES_Schnittstelle", 1, namespace=3)
    root.get_children_descriptions.return_value = _references(wrong_namespace, target)
    nodes = {node.nodeid.to_string(): node for node in [wrong_namespace, target]}
    client.client.get_node.side_effect = lambda node_id: nodes[node_id.to_string()]

    assert client._find_node_by_name_sync(root, "DB_MES_Schnittstelle", 3) is target


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

    with pytest.raises(KeyError, match="Missing.*Available children: 'Alpha'"):
        client._get_child(parent, "Missing")


@pytest.mark.parametrize("plc_name", ["MESAuftragKommisionieren", "MESAuftragKommissionieren"])
def test_delivery_node_resolves_both_confirmed_plc_spellings(plc_name):
    client = _make_client()
    production = _make_mock_node("MESAuftragProduktion")
    delivery = _make_mock_node(plc_name)
    db = MagicMock()
    db.get_children.return_value = [production, delivery]

    assert client._get_child(db, "MESAuftragKommissionieren") is delivery


def test_exact_child_name_takes_precedence_over_alias():
    client = _make_client()
    alias = _make_mock_node("MESAuftragKommisionieren")
    exact = _make_mock_node("MESAuftragKommissionieren")
    db = MagicMock()
    db.get_children.return_value = [alias, exact]

    assert client._get_child(db, "MESAuftragKommissionieren") is exact


def test_missing_delivery_node_does_not_fall_back_to_production():
    client = _make_client()
    db = MagicMock()
    db.get_children.return_value = [_make_mock_node("MESAuftragProduktion")]

    with pytest.raises(KeyError, match="Available children: 'MESAuftragProduktion'"):
        client._get_child(db, "MESAuftragKommissionieren")


# --- read_auftragssteuerung ---

def test_read_auftragssteuerung_returns_mes_command():
    client = _make_client()
    steuerung = _make_mock_node("Auftragssteuerung_MES", value=1)
    hmi = _make_mock_node("Auftragssteuerung_HMI", value=4)
    kopf = _make_mock_node("Kopf")
    kopf.get_children.return_value = [hmi, steuerung]
    root = MagicMock()
    root.get_children.return_value = [kopf]

    assert client.read_auftragssteuerung(root) == 1


@pytest.mark.parametrize("name", ["StatusMES", "Status_MES"])
def test_read_status_mes_reads_feedback(name):
    # The configured status_node must match exactly; no automatic spelling
    # fallback is applied now that the name is user-configurable (spec #32
    # follow-up: structural nodes).
    client = _make_client()
    feedback = _make_mock_node("Feedback")
    feedback.get_children.return_value = [
        _make_mock_node("StatusHMI", value=0),
        _make_mock_node(name, value=5),
    ]
    root = MagicMock()
    root.get_children.return_value = [feedback]

    assert client.read_status_mes(root, status_node=name) == 5


def test_missing_mes_feedback_is_an_error():
    client = _make_client()
    feedback = _make_mock_node("Feedback")
    feedback.get_children.return_value = [_make_mock_node("StatusHMI", value=5)]
    root = MagicMock()
    root.get_children.return_value = [feedback]

    with pytest.raises(KeyError, match="StatusMES"):
        client.read_status_mes(root)


# --- configurable structural node names ---

def test_read_auftragssteuerung_resolves_renamed_structural_nodes():
    client = _make_client()
    steuerung = _make_mock_node("Steuerung_MES_Custom", value=1)
    kopf = _make_mock_node("Header")
    kopf.get_children.return_value = [steuerung]
    root = MagicMock()
    root.get_children.return_value = [kopf]

    assert client.read_auftragssteuerung(
        root, kopf_node="Header", auftragssteuerung_node="Steuerung_MES_Custom"
    ) == 1


def test_write_auftragssteuerung_resolves_renamed_structural_nodes():
    client = _make_client()
    steuerung = _make_mock_node("Steuerung_MES_Custom", vtype=ua.VariantType.Byte)
    kopf = _make_mock_node("Header")
    kopf.get_children.return_value = [steuerung]
    root = MagicMock()
    root.get_children.return_value = [kopf]

    client.write_auftragssteuerung(root, 0, kopf_node="Header", auftragssteuerung_node="Steuerung_MES_Custom")

    steuerung.set_data_value.assert_called_once()
    assert steuerung.set_data_value.call_args[0][0].Value.Value == 0


def test_get_product_queue_item_resolves_a_custom_pattern():
    client = _make_client()
    item = _make_mock_node("Slot[0]")
    inhalt = MagicMock()
    inhalt.get_children.return_value = [item]

    assert client._get_product_queue_item(inhalt, 0, pattern="Slot[{index}]") is item


# --- write_order ---

def _make_order_tree(nested_queue: bool, slots: int = 2, numeric_indices: bool = False):
    # Mirrors the current PLC photos, including independent HMI/MES controls.
    kopf_children = [
        _make_mock_node("Auftragsnummer", vtype=ua.VariantType.UInt16),
        _make_mock_node("Kundennummer", vtype=ua.VariantType.UInt16),
        _make_mock_node("Startdatum", vtype=ua.VariantType.UInt16),
        _make_mock_node("Startzeit", vtype=ua.VariantType.UInt32),
        *[_make_mock_node(n) for n in [
            "AuftragsArt", "Priorität", "Parameter0", "Parameter1",
            "Auftragssteuerung_HMI", "Auftragssteuerung_MES",
        ]],
    ]

    products = []
    for i in range(slots):
        produkt = _make_mock_node(str(i) if numeric_indices else f"Produktqueue[{i}]")
        produkt.get_children.return_value = [
            _make_mock_node("ProduktID"),
            _make_mock_node("Produkttext", vtype=ua.VariantType.String),
            *[_make_mock_node(n, vtype=ua.VariantType.UInt16) for n in [
                "Seriennummer", "Sequenznummer", "Takt",
            ]],
        ]
        products.append(produkt)

    if nested_queue:
        queue = _make_mock_node("Produktqueue")
        queue.get_children.return_value = products
        queue_children = [queue]
    else:
        queue_children = products

    inhalt_children = [
        _make_mock_node("ProduktID"),
        _make_mock_node("Anzahl"),
        _make_mock_node("SeriennummerStart", vtype=ua.VariantType.UInt16),
        *queue_children,
    ]

    kopf = _make_mock_node("Kopf")
    kopf.get_children.return_value = kopf_children
    inhalt = _make_mock_node("Inhalt")
    inhalt.get_children.return_value = inhalt_children
    root = MagicMock()
    root.get_children.return_value = [kopf, inhalt]
    return root, kopf_children, inhalt_children, products


def _make_order():
    return MESAuftrag(
        kopf=AuftragKopf(
            Auftragsnummer=1,
            Startdatum=date(2026, 10, 12),
            Startzeit=time(8, 0),
            Parameter0=7,
            Parameter1=9,
        ),
        inhalt=AuftragInhalt(
            Produktqueue=[
                ProduktDaten(ProduktID=42, Produkttext="First", Seriennummer=1001),
                ProduktDaten(ProduktID=42, Produkttext="Second", Seriennummer=1002),
            ],
        ),
    )


@pytest.mark.parametrize("nested_queue,numeric_indices", [(False, False), (True, False), (True, True)])
@pytest.mark.parametrize("auftragsart", [1, 4])
def test_write_order_uses_current_plc_schema_and_starts_last(nested_queue, numeric_indices, auftragsart):
    client = _make_client()
    root, kopf_children, inhalt_children, products = _make_order_tree(nested_queue, numeric_indices=numeric_indices)
    writes = []
    leaves = kopf_children + inhalt_children[:3]
    for produkt in products:
        leaves += produkt.get_children.return_value
    for node in leaves:
        node.set_data_value.side_effect = lambda dv, n=node: writes.append((n, dv.Value.Value))

    client.write_order(root, _make_order(), auftragsart)

    anzahl_node = next(
        n for n in inhalt_children if n.get_browse_name().Name == "Anzahl"
    )
    anzahl_node.set_data_value.assert_called_once()
    assert anzahl_node.set_data_value.call_args[0][0].Value.Value == 2

    auftragssteuerung_node = next(
        n for n in kopf_children if n.get_browse_name().Name == "Auftragssteuerung_MES"
    )
    auftragssteuerung_node.set_data_value.assert_called_once()
    written_variant = auftragssteuerung_node.set_data_value.call_args[0][0].Value
    assert written_variant.Value == 1
    assert written_variant.VariantType == ua.VariantType.Byte
    assert writes[-1] == (auftragssteuerung_node, 1)
    assert len(writes) == 21  # all header/content/product fields plus the start command
    expected = {"AuftragsArt": auftragsart, "Parameter0": 7, "Parameter1": 9, "Startzeit": 28800000}
    for node in kopf_children:
        name = node.get_browse_name().Name
        if name in expected:
            assert node.set_data_value.call_args[0][0].Value.Value == expected[name]
        elif name == "Auftragssteuerung_HMI":
            node.set_data_value.assert_not_called()
    inhalt_children[0].set_data_value.assert_not_called()
    for index, produkt in enumerate(products):
        fields = {n.get_browse_name().Name: n for n in produkt.get_children()}
        assert fields["ProduktID"].set_data_value.call_args[0][0].Value.Value == 42
        assert fields["Seriennummer"].set_data_value.call_args[0][0].Value.Value == 1001 + index


def test_oversized_queue_is_rejected_before_any_order_write():
    client = _make_client()
    root, kopf_children, inhalt_children, products = _make_order_tree(True, slots=1)

    with pytest.raises(KeyError, match=r"Produktqueue\[1\]"):
        client.write_order(root, _make_order(), auftragsart=1)

    for node in kopf_children + inhalt_children[:3] + products[0].get_children():
        node.set_data_value.assert_not_called()


def test_reset_writes_mes_command_without_changing_hmi_or_feedback():
    client = _make_client()
    root, kopf_children, _, _ = _make_order_tree(True)

    client.write_auftragssteuerung(root, 0)

    for node in kopf_children:
        if node.get_browse_name().Name == "Auftragssteuerung_MES":
            assert node.set_data_value.call_args[0][0].Value.Value == 0
        else:
            node.set_data_value.assert_not_called()


@pytest.mark.parametrize("value,vtype,expected", [
    (date(1990, 1, 1), ua.VariantType.UInt16, 0),
    (date(1990, 1, 2), ua.VariantType.UInt16, 1),
    (date(2168, 12, 31), ua.VariantType.UInt16, 65378),
    (time(0), ua.VariantType.UInt32, 0),
    (time(9), ua.VariantType.UInt32, 32400000),
    (time(23, 59, 59, 999000), ua.VariantType.UInt32, 86399999),
    (date(2026, 10, 12), ua.VariantType.DateTime, datetime(2026, 10, 12)),
    (time(9, 0, 0, 123000), ua.VariantType.DateTime, datetime(1970, 1, 1, 9, 0, 0, 123000)),
])
def test_date_and_time_encoding_matches_plc_types(value, vtype, expected):
    encoded = OpcUaClient._encode_value(value, vtype)
    assert encoded == expected
    variant_to_binary(ua.Variant(encoded, vtype))


@pytest.mark.parametrize("value,vtype", [
    (date(1989, 12, 31), ua.VariantType.UInt16),
    (date(2169, 1, 1), ua.VariantType.UInt16),
    (time(9, tzinfo=timezone.utc), ua.VariantType.UInt32),
    (date(2026, 10, 12), ua.VariantType.Byte),
    (time(9), ua.VariantType.UInt16),
])
def test_invalid_plc_date_time_values_are_rejected(value, vtype):
    with pytest.raises((ValueError, TypeError)):
        OpcUaClient._encode_value(value, vtype)


def test_invalid_field_encoding_is_rejected_before_any_plc_write():
    client = _make_client()
    root, kopf_children, inhalt_children, products = _make_order_tree(True, numeric_indices=True)
    order = _make_order()
    order.kopf.Startdatum = date(1989, 12, 31)

    with pytest.raises(ValueError, match="Startdatum.*1990-01-01"):
        client.write_order(root, order, auftragsart=1)

    for node in kopf_children + inhalt_children[:3]:
        node.set_data_value.assert_not_called()
    for product in products:
        for node in product.get_children():
            node.set_data_value.assert_not_called()
