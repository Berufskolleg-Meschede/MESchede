# OPC UA Order Integration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement full OPC UA order dispatch — Pydantic models for both order types, a generic node walker that writes order data to the PLC, two independent async worker queues (production + delivery), and wired-up REST endpoints.

**Architecture:** Two `asyncio.Queue` + worker pairs run concurrently (one per order type). Each worker polls `Kopf.Auftragssteuerung == 0` to confirm the PLC is free, waits 3 s, writes the full order via a generic field walker on `OpcUaClient`, then polls until `Auftragssteuerung` returns to 0 (done). Both workers reuse the same `MESAuftrag` model since both PLC slots share `typAuftragMES`.

**Tech Stack:** Python 3.12, FastAPI, `opcua` (sync library wrapped in `async def`), Pydantic v2, pytest

## Global Constraints

- `opcua` library calls are synchronous — called directly inside `async def` without executor (matches existing codebase pattern)
- Worker reconnects on any error (existing pattern in `production_queue.py`)
- All errors logged with `order_id` via `logger.exception()`
- No new environment variables — nodes found by browse-name traversal from `DB_MES_Schnittstelle`
- OPC UA browse names are case-sensitive PascalCase (match exactly as shown in PLC printout)

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `backend/app/models/mes_auftrag.py` | **Create** | Pydantic models mirroring `typAuftragMES` |
| `backend/app/clients/opc_ua_client.py` | **Modify** | Add `_get_child`, `read_auftragssteuerung`, `write_order` |
| `backend/app/workers/production_queue.py` | **Modify** | Update payload type, fill out worker stubs, add root node |
| `backend/app/workers/delivery_queue.py` | **Create** | Delivery worker — same pattern, `MESAuftragKommissionieren` root |
| `backend/app/routers/productionorders_router.py` | **Modify** | Replace exploratory code with clean queue enqueue |
| `backend/app/routers/deliveryorders_router.py` | **Modify** | Wire `POST /deliveryorder` to delivery queue |
| `backend/app/main.py` | **Modify** | Start/stop delivery worker in FastAPI lifecycle |
| `backend/tests/test_mes_auftrag.py` | **Create** | Model unit tests |
| `backend/tests/test_opc_ua_client.py` | **Create** | Client helper unit tests |

---

### Task 1: MESAuftrag Pydantic models + pytest setup

**Files:**
- Create: `backend/app/models/mes_auftrag.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_mes_auftrag.py`

**Interfaces:**
- Produces: `MESAuftrag`, `AuftragKopf`, `AuftragInhalt`, `ProduktDaten` — imported by Tasks 2, 3, 4, 5

- [ ] **Step 1: Install pytest**

```bash
cd backend
pip install pytest
```

- [ ] **Step 2: Create `backend/tests/__init__.py`** (empty file)

- [ ] **Step 3: Write the failing tests**

Create `backend/tests/test_mes_auftrag.py`:

```python
from datetime import date, time
import pytest
from app.models.mes_auftrag import MESAuftrag, AuftragKopf, AuftragInhalt, ProduktDaten


def _make_auftrag(auftragsart: int = 1) -> MESAuftrag:
    return MESAuftrag(
        kopf=AuftragKopf(
            Auftragsnummer=1,
            Startdatum=date(2026, 6, 23),
            Startzeit=time(8, 0),
            AuftragsArt=auftragsart,
        ),
        inhalt=AuftragInhalt(ProduktID=42, Anzahl=5),
    )


def test_mes_auftrag_defaults():
    order = _make_auftrag()
    assert order.kopf.Prioritaet == 1
    assert order.kopf.Kundennummer == 0
    assert order.kopf.Parameter == 0
    assert order.inhalt.SeriennummerStart == 0
    assert order.inhalt.Produktqueue == []


def test_produkt_daten_defaults():
    p = ProduktDaten()
    assert p.ProduktID == 0
    assert p.Produkttext == ""
    assert p.Seriennummer == 0


def test_produkt_queue_populated():
    order = MESAuftrag(
        kopf=AuftragKopf(
            Auftragsnummer=2,
            Startdatum=date(2026, 6, 23),
            Startzeit=time(9, 0),
            AuftragsArt=4,
        ),
        inhalt=AuftragInhalt(
            ProduktID=7,
            Anzahl=2,
            Produktqueue=[
                ProduktDaten(ProduktID=7, Produkttext="Artikel A", Seriennummer=1001),
                ProduktDaten(ProduktID=7, Produkttext="Artikel A", Seriennummer=1002),
            ],
        ),
    )
    assert len(order.inhalt.Produktqueue) == 2
    assert order.inhalt.Produktqueue[0].Seriennummer == 1001
```

- [ ] **Step 4: Run — expect ImportError (module not yet created)**

```bash
cd backend
python -m pytest tests/test_mes_auftrag.py -v
```

Expected: `ModuleNotFoundError: No module named 'app.models.mes_auftrag'`

- [ ] **Step 5: Create `backend/app/models/mes_auftrag.py`**

```python
from datetime import date, time
from pydantic import BaseModel


class ProduktDaten(BaseModel):
    Produkttext: str = ""
    ProduktID: int = 0
    Seriennummer: int = 0
    Sequenznummer: int = 0
    Takt: int = 0


class AuftragInhalt(BaseModel):
    ProduktID: int
    Anzahl: int
    SeriennummerStart: int = 0
    Produktqueue: list[ProduktDaten] = []


class AuftragKopf(BaseModel):
    Auftragsnummer: int
    Kundennummer: int = 0
    Startdatum: date
    Startzeit: time
    AuftragsArt: int  # 1=Produktion, 4=Kommissionieren
    Prioritaet: int = 1  # 0=Niedrig, 1=Normal, 2=Hoch — maps to OPC UA node "Priorität"
    Parameter: int = 0
    # Auftragssteuerung is NOT in the model — worker writes it directly


class MESAuftrag(BaseModel):
    kopf: AuftragKopf
    inhalt: AuftragInhalt
```

- [ ] **Step 6: Run — expect all pass**

```bash
cd backend
python -m pytest tests/test_mes_auftrag.py -v
```

Expected: 3 tests PASSED

- [ ] **Step 7: Commit**

```bash
git add backend/app/models/mes_auftrag.py backend/tests/
git commit -m "feat: add MESAuftrag Pydantic models and pytest setup"
```

---

### Task 2: OpcUaClient node helpers

**Files:**
- Modify: `backend/app/clients/opc_ua_client.py`
- Create: `backend/tests/test_opc_ua_client.py`

**Interfaces:**
- Consumes: `MESAuftrag` from Task 1
- Produces:
  - `OpcUaClient._get_child(node, browse_name: str)` → node (sync)
  - `OpcUaClient.read_auftragssteuerung(root_node) -> int` (sync)
  - `OpcUaClient.write_order(root_node, order: MESAuftrag) -> None` (sync)

- [ ] **Step 1: Write the failing tests**

Create `backend/tests/test_opc_ua_client.py`:

```python
from datetime import date, time
from unittest.mock import MagicMock, call
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

    # Build a minimal mock tree: root → Kopf → {Auftragsnummer, Kundennummer,
    # Startdatum, Startzeit, AuftragsArt, Priorität, Parameter, Auftragssteuerung}
    # root → Inhalt → {ProduktID, Anzahl, SeriennummerStart}
    def make_kopf_children():
        names = [
            "Auftragsnummer", "Kundennummer", "Startdatum", "Startzeit",
            "AuftragsArt", "Priorität", "Parameter", "Auftragssteuerung",
        ]
        return [_make_mock_node(n) for n in names]

    def make_inhalt_children():
        return [_make_mock_node(n) for n in ["ProduktID", "Anzahl", "SeriennummerStart"]]

    kopf_children = make_kopf_children()
    inhalt_children = make_inhalt_children()

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
            AuftragsArt=1,
        ),
        inhalt=AuftragInhalt(ProduktID=42, Anzahl=5),
    )

    client.write_order(root, order)

    # The Auftragssteuerung node is the last child in kopf_children
    auftragssteuerung_node = next(
        n for n in kopf_children if n.get_browse_name().Name == "Auftragssteuerung"
    )
    auftragssteuerung_node.set_data_value.assert_called_once()
    written_variant = auftragssteuerung_node.set_data_value.call_args[0][0].Value
    assert written_variant.Value == 1
```

- [ ] **Step 2: Run — expect AttributeError (methods not yet added)**

```bash
cd backend
python -m pytest tests/test_opc_ua_client.py -v
```

Expected: `AttributeError: '_get_child'` or similar

- [ ] **Step 3: Add helpers to `backend/app/clients/opc_ua_client.py`**

Add these imports at the top (after existing imports):

```python
from datetime import date, time as dt_time, datetime
from opcua import ua
from .base import ProductionClient
from ..models.mes_auftrag import MESAuftrag
```

Then add these methods to `OpcUaClient` (before `call_method`):

```python
_FIELD_NAME_MAP = {"Prioritaet": "Priorität"}

def _get_child(self, node, browse_name: str):
    for child in node.get_children():
        if child.get_browse_name().Name == browse_name:
            return child
    raise KeyError(f"OPC UA child node not found: {browse_name!r}")

def read_auftragssteuerung(self, root_node) -> int:
    kopf = self._get_child(root_node, "Kopf")
    return self._get_child(kopf, "Auftragssteuerung").get_value()

def _write_field(self, parent_node, browse_name: str, value) -> None:
    opc_name = self._FIELD_NAME_MAP.get(browse_name, browse_name)
    node = self._get_child(parent_node, opc_name)
    existing_vtype = node.get_data_value().Value.VariantType
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime(value.year, value.month, value.day)
    elif isinstance(value, dt_time):
        value = datetime(1970, 1, 1, value.hour, value.minute, value.second)
    node.set_data_value(ua.DataValue(ua.Variant(value, existing_vtype)))

def write_order(self, root_node, order: MESAuftrag) -> None:
    kopf_node = self._get_child(root_node, "Kopf")
    for field_name, value in order.kopf.model_dump().items():
        self._write_field(kopf_node, field_name, value)

    inhalt_node = self._get_child(root_node, "Inhalt")
    for field_name in ("ProduktID", "Anzahl", "SeriennummerStart"):
        self._write_field(inhalt_node, field_name, getattr(order.inhalt, field_name))

    for i, produkt in enumerate(order.inhalt.Produktqueue):
        item_node = self._get_child(inhalt_node, f"Produktqueue[{i}]")
        for field_name, value in produkt.model_dump().items():
            self._write_field(item_node, field_name, value)

    auftragssteuerung_node = self._get_child(kopf_node, "Auftragssteuerung")
    auftragssteuerung_node.set_data_value(
        ua.DataValue(ua.Variant(1, ua.VariantType.Byte))
    )
```

> **Note:** `order.kopf.model_dump()` includes `Prioritaet`. `_FIELD_NAME_MAP` translates it to `Priorität` when calling `_write_field`. `Auftragssteuerung` is not in `AuftragKopf` so it is not written during the field loop — it is written explicitly at the end with value `1`.

- [ ] **Step 4: Run — expect all pass**

```bash
cd backend
python -m pytest tests/test_opc_ua_client.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/app/clients/opc_ua_client.py backend/app/models/mes_auftrag.py backend/tests/test_opc_ua_client.py
git commit -m "feat: add OpcUaClient node helpers (_get_child, read_auftragssteuerung, write_order)"
```

---

### Task 3: Fill out production_queue.py

**Files:**
- Modify: `backend/app/workers/production_queue.py`

**Interfaces:**
- Consumes: `MESAuftrag` (Task 1), `OpcUaClient.read_auftragssteuerung`, `OpcUaClient.write_order` (Task 2)
- Produces: `ProductionOrderPayload` (updated — `mes_auftrag: MESAuftrag` field), `order_queue`, `start_worker`, `stop_worker` — imported by Task 5

- [ ] **Step 1: Replace `production_queue.py` entirely**

```python
import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from ..clients.opc_ua_client import OpcUaClient
from ..models.mes_auftrag import MESAuftrag

logger = logging.getLogger(__name__)


class ProductionOrderPayload(BaseModel):
    order_id: str
    mes_auftrag: MESAuftrag


order_queue: asyncio.Queue = asyncio.Queue()
_current_order: Optional[ProductionOrderPayload] = None
_worker_task: Optional[asyncio.Task] = None


def get_queue_size() -> int:
    return order_queue.qsize()


def get_current_order_id() -> Optional[str]:
    return _current_order.order_id if _current_order else None


async def start_worker() -> None:
    global _worker_task
    if _worker_task and not _worker_task.done():
        return
    _worker_task = asyncio.create_task(_worker_loop())


async def stop_worker() -> None:
    global _worker_task
    if not _worker_task:
        return
    _worker_task.cancel()
    try:
        await _worker_task
    except asyncio.CancelledError:
        pass
    _worker_task = None


async def _worker_loop() -> None:
    opc_client: Optional[OpcUaClient] = None
    root_node = None
    try:
        while True:
            if opc_client is None:
                try:
                    opc_client = await _create_client()
                    root_node = await _get_root_node(opc_client)
                except Exception:
                    logger.exception("Failed to create OPC UA client")
                    await asyncio.sleep(2.0)
                    continue
            order = await order_queue.get()
            global _current_order
            _current_order = order
            try:
                await _wait_for_plc_ready(opc_client, root_node)
                await asyncio.sleep(3.0)
                await _send_order(opc_client, root_node, order)
                await _wait_for_plc_done(opc_client, root_node)
                logger.info("Order processed", extra={"order_id": order.order_id})
            except Exception:
                logger.exception("Order processing failed", extra={"order_id": order.order_id})
                try:
                    await opc_client.disconnect()
                except Exception:
                    logger.exception("Failed to disconnect after error")
                opc_client = None
                root_node = None
            finally:
                _current_order = None
                order_queue.task_done()
    except asyncio.CancelledError:
        raise
    finally:
        if opc_client is not None:
            try:
                await opc_client.disconnect()
            except Exception:
                logger.exception("Failed to disconnect during shutdown")


async def _create_client() -> OpcUaClient:
    load_dotenv()
    opc_ua_url = os.getenv("OPC_UA_URL")
    if not opc_ua_url:
        raise RuntimeError("OPC_UA_URL is not set")
    client = OpcUaClient(opc_ua_url)
    if await client.connect() is False:
        raise RuntimeError("Failed to connect to OPC UA server")
    return client


async def _get_root_node(opc_client: OpcUaClient):
    db_node = await opc_client.find_db_mes_schnittstelle()
    return opc_client._get_child(db_node, "MESAuftragProduktion")


async def _wait_for_plc_ready(opc_client: OpcUaClient, root_node, timeout_s: float = 30.0) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    while True:
        if opc_client.read_auftragssteuerung(root_node) == 0:
            return
        if loop.time() - start >= timeout_s:
            raise TimeoutError("PLC not ready within timeout")
        await asyncio.sleep(0.5)


async def _send_order(opc_client: OpcUaClient, root_node, order: ProductionOrderPayload) -> None:
    opc_client.write_order(root_node, order.mes_auftrag)


async def _wait_for_plc_done(opc_client: OpcUaClient, root_node, timeout_s: float = 600.0) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    while True:
        if opc_client.read_auftragssteuerung(root_node) == 0:
            return
        if loop.time() - start >= timeout_s:
            raise TimeoutError("PLC did not finish within timeout")
        await asyncio.sleep(0.5)
```

- [ ] **Step 2: Verify import resolves**

```bash
cd backend
python -c "from app.workers.production_queue import ProductionOrderPayload, order_queue; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/workers/production_queue.py
git commit -m "feat: implement production worker queue with OPC UA polling and order dispatch"
```

---

### Task 4: Create delivery_queue.py

**Files:**
- Create: `backend/app/workers/delivery_queue.py`

**Interfaces:**
- Consumes: `MESAuftrag` (Task 1), `OpcUaClient.read_auftragssteuerung`, `OpcUaClient.write_order` (Task 2)
- Produces: `DeliveryOrderPayload`, `delivery_queue`, `start_delivery_worker`, `stop_delivery_worker` — imported by Tasks 5, main.py

- [ ] **Step 1: Create `backend/app/workers/delivery_queue.py`**

```python
import asyncio
import logging
import os
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel

from ..clients.opc_ua_client import OpcUaClient
from ..models.mes_auftrag import MESAuftrag

logger = logging.getLogger(__name__)


class DeliveryOrderPayload(BaseModel):
    order_id: str
    mes_auftrag: MESAuftrag


delivery_queue: asyncio.Queue = asyncio.Queue()
_current_delivery: Optional[DeliveryOrderPayload] = None
_delivery_worker_task: Optional[asyncio.Task] = None


def get_delivery_queue_size() -> int:
    return delivery_queue.qsize()


def get_current_delivery_order_id() -> Optional[str]:
    return _current_delivery.order_id if _current_delivery else None


async def start_delivery_worker() -> None:
    global _delivery_worker_task
    if _delivery_worker_task and not _delivery_worker_task.done():
        return
    _delivery_worker_task = asyncio.create_task(_worker_loop())


async def stop_delivery_worker() -> None:
    global _delivery_worker_task
    if not _delivery_worker_task:
        return
    _delivery_worker_task.cancel()
    try:
        await _delivery_worker_task
    except asyncio.CancelledError:
        pass
    _delivery_worker_task = None


async def _worker_loop() -> None:
    opc_client: Optional[OpcUaClient] = None
    root_node = None
    try:
        while True:
            if opc_client is None:
                try:
                    opc_client = await _create_client()
                    root_node = await _get_root_node(opc_client)
                except Exception:
                    logger.exception("Failed to create OPC UA client (delivery)")
                    await asyncio.sleep(2.0)
                    continue
            order = await delivery_queue.get()
            global _current_delivery
            _current_delivery = order
            try:
                await _wait_for_plc_ready(opc_client, root_node)
                await asyncio.sleep(3.0)
                await _send_order(opc_client, root_node, order)
                await _wait_for_plc_done(opc_client, root_node)
                logger.info("Delivery order processed", extra={"order_id": order.order_id})
            except Exception:
                logger.exception("Delivery order processing failed", extra={"order_id": order.order_id})
                try:
                    await opc_client.disconnect()
                except Exception:
                    logger.exception("Failed to disconnect after delivery error")
                opc_client = None
                root_node = None
            finally:
                _current_delivery = None
                delivery_queue.task_done()
    except asyncio.CancelledError:
        raise
    finally:
        if opc_client is not None:
            try:
                await opc_client.disconnect()
            except Exception:
                logger.exception("Failed to disconnect delivery worker during shutdown")


async def _create_client() -> OpcUaClient:
    load_dotenv()
    opc_ua_url = os.getenv("OPC_UA_URL")
    if not opc_ua_url:
        raise RuntimeError("OPC_UA_URL is not set")
    client = OpcUaClient(opc_ua_url)
    if await client.connect() is False:
        raise RuntimeError("Failed to connect to OPC UA server")
    return client


async def _get_root_node(opc_client: OpcUaClient):
    db_node = await opc_client.find_db_mes_schnittstelle()
    return opc_client._get_child(db_node, "MESAuftragKommissionieren")


async def _wait_for_plc_ready(opc_client: OpcUaClient, root_node, timeout_s: float = 30.0) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    while True:
        if opc_client.read_auftragssteuerung(root_node) == 0:
            return
        if loop.time() - start >= timeout_s:
            raise TimeoutError("PLC not ready within timeout (delivery)")
        await asyncio.sleep(0.5)


async def _send_order(opc_client: OpcUaClient, root_node, order: DeliveryOrderPayload) -> None:
    opc_client.write_order(root_node, order.mes_auftrag)


async def _wait_for_plc_done(opc_client: OpcUaClient, root_node, timeout_s: float = 600.0) -> None:
    loop = asyncio.get_running_loop()
    start = loop.time()
    while True:
        if opc_client.read_auftragssteuerung(root_node) == 0:
            return
        if loop.time() - start >= timeout_s:
            raise TimeoutError("PLC did not finish within timeout (delivery)")
        await asyncio.sleep(0.5)
```

- [ ] **Step 2: Verify import resolves**

```bash
cd backend
python -c "from app.workers.delivery_queue import DeliveryOrderPayload, delivery_queue; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/app/workers/delivery_queue.py
git commit -m "feat: add delivery order worker queue for MESAuftragKommissionieren"
```

---

### Task 5: Wire routers + update main.py

**Files:**
- Modify: `backend/app/routers/productionorders_router.py`
- Modify: `backend/app/routers/deliveryorders_router.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Consumes: `ProductionOrderPayload`, `order_queue` (Task 3); `DeliveryOrderPayload`, `delivery_queue` (Task 4)

- [ ] **Step 1: Replace `productionorders_router.py`**

```python
from fastapi import APIRouter, status

from ..workers.production_queue import ProductionOrderPayload, order_queue

router = APIRouter(prefix="/productionorder", tags=["productionorder"])


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post_productionorder(payload: ProductionOrderPayload):
    await order_queue.put(payload)
    return {
        "queued": True,
        "order_id": payload.order_id,
        "queue_size": order_queue.qsize(),
    }
```

- [ ] **Step 2: Replace the `POST /deliveryorder` endpoint in `deliveryorders_router.py`**

Replace only the `post_deliveryorder` function and add the import — keep the other stub routes unchanged:

```python
from fastapi import APIRouter, status

from ..workers.delivery_queue import DeliveryOrderPayload, delivery_queue

router = APIRouter(prefix="/deliveryorder", tags=["deliveryorder"])


@router.get("/")
def list_deliveryorders():
    raise NotImplementedError("Method not implemented yet.")


@router.get("/{deliveryorder_id}")
def get_deliveryorder(deliveryorder_id: str):
    raise NotImplementedError("Method not implemented yet.")


@router.post("/", status_code=status.HTTP_202_ACCEPTED)
async def post_deliveryorder(payload: DeliveryOrderPayload):
    await delivery_queue.put(payload)
    return {
        "queued": True,
        "order_id": payload.order_id,
        "queue_size": delivery_queue.qsize(),
    }


@router.patch("/{deliveryorder_id}")
def patch_deliveryorder(deliveryorder_id: str):
    raise NotImplementedError("Method not implemented yet.")


@router.delete("/{deliveryorder_id}")
def delete_deliveryorder(deliveryorder_id: str):
    raise NotImplementedError("Method not implemented yet.")
```

- [ ] **Step 3: Update `backend/app/main.py`** to start/stop delivery worker

```python
from fastapi import FastAPI

from .routers import sites_router, storage_router, productionorders_router, deliveryorders_router
from .workers.production_queue import start_worker, stop_worker
from .workers.delivery_queue import start_delivery_worker, stop_delivery_worker

app = FastAPI()


@app.on_event("startup")
async def start_background_workers() -> None:
    await start_worker()
    await start_delivery_worker()


@app.on_event("shutdown")
async def stop_background_workers() -> None:
    await stop_worker()
    await stop_delivery_worker()


app.include_router(router=sites_router.router)
app.include_router(router=storage_router.router)
app.include_router(router=productionorders_router.router)
app.include_router(router=deliveryorders_router.router)
```

- [ ] **Step 4: Run all tests**

```bash
cd backend
python -m pytest tests/ -v
```

Expected: all tests PASSED

- [ ] **Step 5: Smoke-test that FastAPI starts without import errors**

```bash
cd backend
python -c "from app.main import app; print('FastAPI app imports OK')"
```

Expected: `FastAPI app imports OK`

- [ ] **Step 6: Commit**

```bash
git add backend/app/routers/productionorders_router.py backend/app/routers/deliveryorders_router.py backend/app/main.py
git commit -m "feat: wire production and delivery order endpoints to worker queues"
```

---

## Self-Review

**Spec coverage:**
- ✅ Two independent queue/worker pairs
- ✅ `MESAuftrag`, `AuftragKopf`, `AuftragInhalt`, `ProduktDaten` models
- ✅ `_get_child`, `read_auftragssteuerung`, `write_order` on `OpcUaClient`
- ✅ Poll `Auftragssteuerung == 0` before sending (30s timeout)
- ✅ 3-second rest buffer before writing
- ✅ Poll `Auftragssteuerung == 0` after sending (600s timeout)
- ✅ Error → disconnect → reconnect on next order
- ✅ Both workers start/stop in FastAPI lifecycle
- ✅ `Prioritaet` → `Priorität` FIELD_NAME_MAP
- ✅ `Auftragssteuerung` excluded from model, written explicitly as `1` after other fields

**Type consistency:**
- `ProductionOrderPayload.mes_auftrag: MESAuftrag` — consistent across Task 3 and Task 5
- `DeliveryOrderPayload.mes_auftrag: MESAuftrag` — consistent across Task 4 and Task 5
- `_get_child` used consistently in Task 2 (implementation), Task 3 (`_get_root_node`), Task 4 (`_get_root_node`)
- `write_order(root_node, order: MESAuftrag)` — consistent across Task 2 (definition) and Tasks 3/4 (`_send_order` calls)
