# OPC UA Order Integration Design

**Date:** 2026-06-23
**Branch:** opc-ua-functionality

## Context

MESchede communicates with a factory simulation PLC over OPC UA. The PLC exposes a `DB_MES_Schnittstelle` data block with two order slots of type `typAuftragMES`:

- `MESAuftragProduktion` — MES writes production orders (make new products)
- `MESAuftragKommissionieren` — MES writes delivery/commission orders (pick from storage)

Both slots share the same node structure. The key control field is `Kopf.Auftragssteuerung` (USInt):

| Value | Meaning |
|-------|---------|
| 0 | Kein Auftrag — machine free, ready for next order |
| 1 | Start — MES triggers PLC to begin |
| 2 | Unterbrechen — pause |
| 3 | Neustart — restart |
| 4 | Abbrechen — abort |
| 5 | Fertig — done |

Production and delivery orders run independently and in parallel on the same machine.

## Architecture

Two independent async queue/worker pairs, one per order type:

```
POST /productionorder → production_queue (asyncio.Queue) → production worker
                                                            ↓ root: MESAuftragProduktion
POST /deliveryorder   → delivery_queue   (asyncio.Queue) → delivery worker
                                                            ↓ root: MESAuftragKommissionieren
```

Both workers start and stop with the FastAPI lifecycle via `main.py` `startup`/`shutdown` events.

## OPC UA Node Structure

Both root nodes share `typAuftragMES`:

```
<root>  (MESAuftragProduktion | MESAuftragKommissionieren)
├── Kopf  (typAuftragKopf)
│   ├── Auftragsnummer      UInt
│   ├── Kundennummer        UInt
│   ├── Startdatum          Date
│   ├── Startzeit           Time_Of_Day
│   ├── AuftragsArt         USInt  (1=Produktion, 2=Einlagern, 3=Direktlieferung, 4=Kommissionieren)
│   ├── Priorität           USInt  (0=Niedrig, 1=Normal, 2=Hoch)
│   ├── Auftragssteuerung   USInt  (0=free, 1=Start, 2=Pause, 3=Restart, 4=Abort, 5=Done)
│   └── Parameter           USInt
└── Inhalt  (typAuftragInhalt)
    ├── ProduktID           USInt
    ├── Anzahl              USInt
    ├── SeriennummerStart   UInt
    └── Produktqueue        Array of typProduktdaten
        └── Produktqueue[n]
            ├── Produkttext       String[32]
            ├── ProduktID         USInt
            ├── Seriennummer      UInt
            ├── Sequenznummer     UInt
            ├── Takt              UInt
            ├── Status            USInt  (0=Ungültig, 1=OK, 2=Deckel fehlt, 3=Gehaeuse falsch, 4=Watchdogfehler)
            ├── Fehlercode        USInt
            ├── Endkontrolle      USInt
            ├── Lagerfach         USInt
            ├── Produktionsdatum  Date_And_Time
            └── Nachverfolgung    typProduktnachverfolgung
```

## Files to Create / Modify

| File | Change |
|------|--------|
| `app/models/mes_auftrag.py` | New — Pydantic models for order payloads |
| `app/clients/opc_ua_client.py` | Add `write_order`, `read_auftragssteuerung`, `_get_child` |
| `app/workers/production_queue.py` | Fill out `_wait_for_plc_ready`, `_send_order`, `_wait_for_plc_done` |
| `app/workers/delivery_queue.py` | New — identical pattern to production_queue for delivery orders |
| `app/routers/deliveryorders_router.py` | Wire up `POST /deliveryorder` to enqueue |
| `app/routers/productionorders_router.py` | Clean up exploratory code, wire up queue |
| `app/main.py` | Start/stop delivery worker alongside production worker |

## Payload Models — `app/models/mes_auftrag.py`

Pydantic models mirror the PLC type definitions. Field names match OPC UA browse names exactly (PascalCase) so the generic walker can use them directly. `Priorität` is the only exception — Python field name is `Prioritaet`, mapped to OPC UA browse name `Priorität` in the walker.

```python
class ProduktDaten(BaseModel):       # typProduktdaten
    Produkttext: str = ""
    ProduktID: int = 0
    Seriennummer: int = 0
    Sequenznummer: int = 0
    Takt: int = 0

class AuftragInhalt(BaseModel):      # typAuftragInhalt
    ProduktID: int
    Anzahl: int
    SeriennummerStart: int = 0
    Produktqueue: list[ProduktDaten] = []

class AuftragKopf(BaseModel):        # typAuftragKopf  (Auftragssteuerung excluded — worker writes it)
    Auftragsnummer: int
    Kundennummer: int = 0
    Startdatum: date
    Startzeit: time
    AuftragsArt: int                 # 1=Produktion, 4=Kommissionieren
    Prioritaet: int = 1              # maps to OPC UA node "Priorität"
    Parameter: int = 0

class MESAuftrag(BaseModel):
    kopf: AuftragKopf
    inhalt: AuftragInhalt
```

`Auftragssteuerung` is not part of the payload model — the worker writes it explicitly to `1` after writing all other fields.

## OpcUaClient Methods

### `_get_child(node, browse_name: str)`
Iterates `node.get_children()` and returns the first child whose `get_browse_name().Name == browse_name`. Raises `KeyError` if not found.

### `read_auftragssteuerung(root_node) -> int`
Navigates `root_node → Kopf → Auftragssteuerung` and returns the integer value.

### `write_order(root_node, order: MESAuftrag) -> None`
Generic walker that writes all fields, then triggers the PLC:

1. Navigate to `Kopf` child node
2. For each field in `order.kopf` (excluding `Auftragssteuerung`): find matching child node by field name (using `FIELD_NAME_MAP = {"Prioritaet": "Priorität"}` for the umlaut), set value with correct OPC UA variant type
3. Navigate to `Inhalt` child node
4. Write `ProduktID`, `Anzahl`, `SeriennummerStart`
5. For each item in `order.inhalt.Produktqueue`: navigate to `Produktqueue[i]` child, write its fields
6. Write `Kopf → Auftragssteuerung = 1` (USInt/Byte) to start the PLC

All `opcua` library calls are synchronous. Following the existing pattern in `opc_ua_client.py`, they are called directly inside `async def` methods (no executor wrapping). For a school project with low concurrency this is acceptable.

## Worker Flow (same for both queues)

```
on startup:
  connect OPC UA client (retry with 2s backoff on failure)

loop:
  order = await queue.get()
  _wait_for_plc_ready(client, root_node, timeout=30s)
    → poll read_auftragssteuerung() every 0.5s until == 0
  await asyncio.sleep(3.0)          ← PLC rest buffer
  _send_order(client, root_node, order)
    → client.write_order(root_node, order)
  _wait_for_plc_done(client, root_node, timeout=600s)
    → poll read_auftragssteuerung() every 0.5s until == 0
  queue.task_done()

on error:
  disconnect client, set client=None → reconnect on next iteration

on shutdown:
  disconnect client
```

Production worker uses `client.find_db_mes_schnittstelle()` then navigates to `MESAuftragProduktion`; delivery worker navigates to `MESAuftragKommissionieren`.

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPC_UA_URL` | OPC UA server endpoint (already used) |

No new env vars needed — root nodes are found by browse name traversal.

## Error Handling

- Connection failure on startup: retry with 2s sleep (already in production_queue.py)
- `_wait_for_plc_ready` timeout (30s): raise `TimeoutError`, order is dropped and logged
- `_wait_for_plc_done` timeout (600s): raise `TimeoutError`, disconnect and reconnect
- Node not found during `write_order`: raise `KeyError`, order is dropped and logged
- All errors are logged with `order_id` for traceability
