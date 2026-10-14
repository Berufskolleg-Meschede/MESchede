import logging
from collections import deque
from datetime import date, time as dt_time, datetime
from typing import Any

from opcua import Client, ua
from opcua.ua.ua_binary import variant_to_binary
from .base import ProductionClient
from .execution import run_opc
from ..models.mes_auftrag import MESAuftrag

logger = logging.getLogger(__name__)


class OpcUaClient(ProductionClient):
    _FIELD_NAME_MAP = {"Prioritaet": "Priorität"}
    _CHILD_NAME_ALIASES = {
        # The current PLC uses one 's' in Kommisionieren (confirmed in IMG_7165).
        "MESAuftragKommissionieren": ("MESAuftragKommisionieren",),
        # Some PLC exports spell the feedback status field with an underscore.
        "StatusMES": ("Status_MES",),
    }

    def __init__(self, url: str) -> None:
        self.client = Client(url)

    async def connect(self):
        try:
            await run_opc(self.client.connect)
            print("Connected to OPC UA server")
        except Exception as e:
            print(f"Error connecting to OPC UA server: {e}")
            return False

    async def disconnect(self):
        try:
            await run_opc(self.client.disconnect)
            print("Disconnected from OPC UA server")
        except Exception as e:
            print(f"Error disconnecting from OPC UA server: {e}")
            return False

    async def browse_nodes(self, node=None):
        if node is None:
            node = self.client.get_root_node()
        print(f"Node: {node.get_display_name().Text} | NodeId: {node.nodeid}")
        try:
            children = node.get_children()
            for child in children:
                print(child.get_display_name().Text)
                await self.browse_nodes(child)
        except Exception:
            pass  # Node might not have children

    async def find_node_by_name(
        self,
        name: str,
        namespace_index: int | None = None,
        node=None,
    ):
        root = node if node is not None else self.client.get_objects_node()
        logger.info("Looking for OPC UA node %s", name)
        return await run_opc(self._find_node_by_name_sync, root, name, namespace_index)

    def _find_node_by_name_sync(self, node, name: str, namespace_index: int | None):
        browse_name = node.get_browse_name()
        if (
            (namespace_index is None or browse_name.NamespaceIndex == namespace_index)
            and (browse_name.Name == name or (
                namespace_index is None and node.get_display_name().Text == name
            ))
        ):
            return node

        # The OPC UA address space is a graph. Breadth-first browsing avoids
        # descending through a large unrelated branch before reaching PLC DBs;
        # visited IDs prevent cycles and duplicate traversal of shared nodes.
        pending = deque([node])
        visited = {node.nodeid.to_string()}
        while pending:
            current = pending.popleft()
            # Browse responses already contain names, avoiding two additional
            # Read requests for every node merely to discover its name.
            for reference in current.get_children_descriptions():
                browse_name = reference.BrowseName
                if (
                    (namespace_index is None or browse_name.NamespaceIndex == namespace_index)
                    and (browse_name.Name == name or (
                        namespace_index is None and reference.DisplayName.Text == name
                    ))
                ):
                    found = self.client.get_node(reference.NodeId)
                    logger.info("Found OPC UA node %s: %s", name, reference.NodeId)
                    return found
                node_id = reference.NodeId.to_string()
                if node_id not in visited:
                    visited.add(node_id)
                    pending.append(self.client.get_node(reference.NodeId))

        logger.warning("OPC UA node %s not found after browsing %s nodes", name, len(visited))
        return None

    async def find_db_mes_schnittstelle(self, namespace_index: int | None = None):
        return await self.find_node_by_name("DB_MES_Schnittstelle", namespace_index)

    def _get_child(self, node, browse_name: str):
        children = [(child, child.get_browse_name().Name) for child in node.get_children()]
        candidates = (browse_name, *self._CHILD_NAME_ALIASES.get(browse_name, ()))
        for candidate in candidates:
            for child, actual_name in children:
                if actual_name == candidate:
                    if candidate != browse_name:
                        logger.info(
                            "OPC UA child %s resolved using PLC spelling %s", browse_name, candidate
                        )
                    return child
        available = ", ".join(repr(name) for _, name in children) or "(none)"
        raise KeyError(
            f"OPC UA child node not found: {browse_name!r} under {node.nodeid}. "
            f"Available children: {available}"
        )

    def read_auftragssteuerung(
        self, root_node, kopf_node: str = "Kopf", auftragssteuerung_node: str = "Auftragssteuerung_MES"
    ) -> int:
        kopf = self._get_child(root_node, kopf_node)
        return self._get_child(kopf, auftragssteuerung_node).get_value()

    def read_anzahl(self, root_node, inhalt_node: str = "Inhalt") -> int:
        inhalt = self._get_child(root_node, inhalt_node)
        return self._get_child(inhalt, "Anzahl").get_value()

    def write_anzahl(self, root_node, value: int, inhalt_node: str = "Inhalt") -> None:
        inhalt = self._get_child(root_node, inhalt_node)
        self._write_field(inhalt, "Anzahl", value)

    def read_status_mes(
        self, root_node, feedback_node: str = "Feedback", status_node: str = "StatusMES"
    ) -> int:
        feedback = self._get_child(root_node, feedback_node)
        return self._get_child(feedback, status_node).get_value()

    def write_auftragssteuerung(
        self, root_node, value: int, kopf_node: str = "Kopf", auftragssteuerung_node: str = "Auftragssteuerung_MES"
    ) -> None:
        kopf = self._get_child(root_node, kopf_node)
        self._write_field(kopf, auftragssteuerung_node, value)

    def clear_product_queue(
        self, root_node, inhalt_node: str = "Inhalt", produktqueue_pattern: str = "Produktqueue[{index}]"
    ) -> None:
        """Clear every exposed slot's MES input fields after confirmed completion.

        Keep PLC-owned tracking/feedback fields untouched. Repeating this after
        a lost response is safe: already cleared fields are only read back.
        """
        inhalt = self._get_child(root_node, inhalt_node)
        container_name = produktqueue_pattern.split("[", 1)[0]
        prefix = f"{container_name}["
        children = inhalt.get_children()
        queue = next((child for child in children
                      if child.get_browse_name().Name == container_name), None)
        candidates = queue.get_children() if queue is not None else children
        slots = []
        for child in candidates:
            name = child.get_browse_name().Name
            if name.startswith(prefix) and name.endswith("]"):
                index = name[len(prefix):-1]
            elif queue is not None:
                index = name
            else:
                continue
            if index.isdecimal():
                slots.append((int(index), child))
        if not slots:
            raise KeyError("OPC UA product queue has no exposed slots to clear")
        defaults = {"ProduktID": 0, "Produkttext": "", "Seriennummer": 0,
                    "Sequenznummer": 0, "Takt": 0}
        # Resolve and validate every field before changing any slot.
        prepared = [self._prepare_field(slot, name, value)
                    for _, slot in sorted(slots, key=lambda item: item[0])
                    for name, value in defaults.items()]
        for node, data_value in prepared:
            expected = data_value.Value.Value
            if node.get_value() != expected:
                node.set_data_value(data_value)
            if node.get_value() != expected:
                raise ValueError(f"PLC queue reset readback mismatch at {node.nodeid}")
        logger.info("PLC queue reset (%s): cleared and verified %s slots", root_node, len(slots))

    def _get_product_queue_item(self, inhalt_node, index: int, pattern: str = "Produktqueue[{index}]"):
        name = pattern.format(index=index)
        container_name = pattern.split("[", 1)[0]
        children = inhalt_node.get_children()
        for child in children:
            if child.get_browse_name().Name == name:
                return child
        for child in children:
            if child.get_browse_name().Name == container_name:
                # The live Siemens server exposes array elements as "0", "1",
                # etc.; TIA Portal displays them as "Produktqueue[0]" instead.
                for item in child.get_children():
                    if item.get_browse_name().Name in (str(index), name):
                        return item
                raise KeyError(f"OPC UA product queue slot not found: {name!r} under {child.nodeid}")
        raise KeyError(f"OPC UA product queue slot not found: {name!r}")

    @staticmethod
    def _encode_value(value, variant_type):
        if isinstance(value, date) and not isinstance(value, datetime):
            if variant_type == ua.VariantType.UInt16:
                # SIMATIC DATE: unsigned days since 1990-01-01.
                days = (value - date(1990, 1, 1)).days
                if not 0 <= days <= 65378:
                    raise ValueError("SIMATIC DATE must be between 1990-01-01 and 2168-12-31")
                return days
            if variant_type == ua.VariantType.DateTime:
                return datetime(value.year, value.month, value.day)
            raise TypeError(f"Cannot encode a date as OPC UA {variant_type.name}")
        if isinstance(value, dt_time):
            if value.tzinfo is not None:
                raise ValueError("PLC time of day must be a local time without a timezone offset")
            if variant_type == ua.VariantType.UInt32:
                # SIMATIC TIME_OF_DAY: unsigned milliseconds since midnight.
                return ((value.hour * 60 + value.minute) * 60 + value.second) * 1000 + value.microsecond // 1000
            if variant_type == ua.VariantType.DateTime:
                return datetime(1970, 1, 1, value.hour, value.minute, value.second, value.microsecond)
            raise TypeError(f"Cannot encode a time as OPC UA {variant_type.name}")
        return value

    def _prepare_field(self, parent_node, browse_name: str, value):
        opc_name = self._FIELD_NAME_MAP.get(browse_name, browse_name)
        node = self._get_child(parent_node, opc_name)
        existing_vtype = node.get_data_value().Value.VariantType
        try:
            value = self._encode_value(value, existing_vtype)
            variant = ua.Variant(value, existing_vtype)
            # Validate with the actual UA binary encoder before sending anything.
            variant_to_binary(variant)
        except Exception as error:
            raise ValueError(
                f"Cannot encode PLC field {opc_name!r} as {existing_vtype.name}: {error}"
            ) from error
        return node, ua.DataValue(variant)

    def _write_field(self, parent_node, browse_name: str, value) -> None:
        node, data_value = self._prepare_field(parent_node, browse_name, value)
        node.set_data_value(data_value)

    def write_order(
        self,
        root_node,
        order: MESAuftrag,
        auftragsart: int,
        kopf_node: str = "Kopf",
        inhalt_node: str = "Inhalt",
        auftragssteuerung_node: str = "Auftragssteuerung_MES",
        produktqueue_pattern: str = "Produktqueue[{index}]",
    ) -> None:
        kopf_node = self._get_child(root_node, kopf_node)
        inhalt_node = self._get_child(root_node, inhalt_node)
        # Resolve all slots before changing order data, so an oversized queue
        # cannot leave a partially written order on the PLC.
        item_nodes = [
            self._get_product_queue_item(inhalt_node, i, produktqueue_pattern)
            for i in range(len(order.inhalt.Produktqueue))
        ]
        fields = [(kopf_node, name, value) for name, value in order.kopf.model_dump().items()]
        fields.extend([
            (kopf_node, "AuftragsArt", auftragsart),
            (inhalt_node, "Anzahl", len(order.inhalt.Produktqueue)),
            (inhalt_node, "SeriennummerStart", order.inhalt.SeriennummerStart),
        ])

        for item_node, produkt in zip(item_nodes, order.inhalt.Produktqueue):
            for field_name, value in produkt.model_dump().items():
                fields.append((item_node, field_name, value))

        fields.append((kopf_node, auftragssteuerung_node, 1))
        prepared = [self._prepare_field(parent, name, value) for parent, name, value in fields]
        for node, data_value in prepared[:-1]:
            node.set_data_value(data_value)

        # Verify the requested quantity and identities before triggering any
        # physical movement. Do not clear unused slots or PLC/HMI-owned fields.
        actual_count = self._get_child(inhalt_node, "Anzahl").get_value()
        if actual_count != len(item_nodes):
            raise ValueError(f"PLC quantity readback mismatch: expected {len(item_nodes)}, got {actual_count}")
        for index, (item_node, produkt) in enumerate(zip(item_nodes, order.inhalt.Produktqueue)):
            for name in ("ProduktID", "Seriennummer"):
                actual = self._get_child(item_node, name).get_value()
                expected = getattr(produkt, name)
                if actual != expected:
                    raise ValueError(f"PLC queue[{index}].{name} readback mismatch: expected {expected}, got {actual}")
        logger.info("PLC order (%s): readback verified, Anzahl=%s; sending MES start", root_node, actual_count)
        start_node, start_value = prepared[-1]
        start_node.set_data_value(start_value)


    async def call_method(self, node_id: str, method: str, args: list[Any]) -> Any:
        pass

    async def call_production_order(self, mes_production_order_node_id: str) -> None:
        pass
