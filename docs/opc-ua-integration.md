# Current OPC UA integration and offline testing

This describes the PLC schema shown in the October 12, 2026 photos and the
confirmed MES handshake. It supersedes the old command-only polling described
in the June integration design.

## Node changes

Both `DB_MES_Schnittstelle.MESAuftragProduktion` and the commissioning slot use
this interface. The commissioning slot is spelled **`MESAuftragKommisionieren`**
(one `s`) in the current PLC screenshots. The client accepts this spelling as
well as `MESAuftragKommissionieren` (two `s`), preferring the exact requested
name if both exist. No other node is used as a fallback.

| Node | MES behavior |
| --- | --- |
| `Kopf.Auftragssteuerung_MES` | Write `1` to start; write `0` after feedback says finished. |
| `Feedback.StatusMES` | Read `0` = idle, `1` = started, `5` = finished. The client also accepts the name `Status_MES`. |
| `Kopf.Parameter0`, `Kopf.Parameter1` | Both are request fields, defaulting to `0`. Legacy request key `Parameter` is accepted as `Parameter0`. |
| `Inhalt.Anzahl` | Derived from the number of `Produktqueue` items, never supplied separately and never written under `Kopf`. |
| `Inhalt.ProduktID` | Unused; deliberately left untouched. Each queue item has its own `ProduktID`. |
| `Inhalt.Produktqueue` | At least one item. The live server exposes numeric child names `0` through `32` inside this node. Each requested slot is resolved before writing order data. Older `Produktqueue[n]` browse names are also supported. |
| `Produktqueue[n].Produkttext` | Maximum 30 characters (`String[30]` in the photos). |
| `Kopf.Startdatum` | Live UA type `UInt16`: encode the ISO request date as days since `1990-01-01`. |
| `Kopf.Startzeit` | Live UA type `UInt32`: encode the request time as milliseconds since midnight. |

The photos show slots `Produktqueue[0]` through `Produktqueue[32]`, i.e. 33
slots. The writer checks the actual browsed slots rather than assuming that
every PLC version has this capacity. Counts are limited to the PLC's USInt range.

The numeric array names and date/time types were verified by a read-only
connection to the real PLC. The conversions follow Siemens' [DATE/TOD
encoding](https://docs.tia.siemens.cloud/r/simatic_s7_1200_manual_collection_dede_20/plc-grundlagen/datentypen/uhrzeit-und-datums-datentypen)
and [S7-1500 OPC UA type mapping](https://docs.tia.siemens.cloud/r/en-us/v20/configuring-automation-systems/using-opc-ua-communication-s7-1200-s7-1500-s7-1500t/using-the-s7-1500-as-an-opc-ua-server-s7-1500-s7-1500t/interesting-information-about-the-opc-ua-server-of-the-s7-1500-cpus-s7-1500-s7-1500t/mapping-simatic-data-types-to-opc-ua-data-types-s7-1500-s7-1500t).
All requested fields are resolved and validated with the UA binary encoder
before any write is sent; the start command remains the last write.

Other visible additions are product fields `Station`, `Position`,
`Fertigungsschritt_Aktuell`, `Fertigungsschritt_Next`, `Parameter`, plus
`Produktionsdatum` now using `DTL`. The photos also show separate HMI control,
`Feedback`, and `Handshake` sections. The MES does not write these additional
fields: the confirmed protocol only needs the MES command and MES feedback.

## Order sequence

1. Wait for MES command `0` and MES feedback `0` (30 s timeout).
   If a previous completed order remains latched at command `1`/feedback `5`
   after a backend restart, acknowledge it by writing command `0` and wait for
   the PLC to confirm idle.
2. After the existing 3 s rest buffer, write the header and all requested queue
   items; write the start command `1` last.
3. Wait for feedback `1` (30 s timeout). Feedback `5` is also accepted here
   because a very short order could finish between polls.
4. Wait for feedback `5` (600 s timeout). Feedback `0` immediately after sending
   start is **not** treated as completion.
5. Write `Kopf.Auftragssteuerung_MES = 0` to acknowledge completion.
6. Confirm both feedback and command return to `0` (30 s timeout), then allow
   the next queued order to start.

Production uses `AuftragsArt=1`; delivery/commissioning uses `AuftragsArt=4`.
Both workers use the same handshake implementation and poll every 0.5 s.
Neither worker writes to the HMI command or any feedback field.

## Test on the isolated IoT network

For PLC tests, use the VS Code **Backend (FastAPI, PLC debugging)** launch
profile, which runs a single server process without `--reload`. Stop the old
debug session before starting it. The ordinary **Backend (FastAPI)** profile
still reloads on source edits; a reload cancels workers and clears queued jobs.
Restart the PLC debugging profile manually after updating code.
Ensure `backend/.env` points `OPC_UA_URL` at the PLC endpoint accessible from
the IoT network. Local API calls do not require Internet; FastAPI's default
Swagger page may require Internet for its CDN assets.

From the `backend` directory, submit the saved one-item request without Swagger:

```bash
curl --fail-with-body -i \
  -X POST http://127.0.0.1:8000/productionorder/ \
  -H 'Content-Type: application/json' \
  --data-binary @examples/production-order.json
```

Set the request's date/time and product ID to appropriate test values first.
The example does not send `Inhalt.ProduktID` or `Anzahl`.

Observe `Inhalt.Anzahl=1`, the contents of `Produktqueue[0]`, command `1`,
feedback `1`, feedback `5`, then command `0` and feedback `0`. The VS Code
terminal logs changes to MES feedback and the reset confirmation. `202` means
queued in memory, not successful dispatch or production completion.

Library packet/browse/read messages are suppressed at INFO level; OPC UA
warnings and errors remain visible. On startup, expect `Looking for OPC UA node
DB_MES_Schnittstelle`, followed by a `Found OPC UA node` message. Discovery
searches the Objects tree breadth-first and visits each node ID once, avoiding
the unrelated Types tree and cycles in the address space. A connection message
alone does not confirm that the order nodes were found.

If a POST returns `202` but the PLC does not change, read the local worker
snapshot (these calls do not contact or write the PLC):

```bash
curl http://127.0.0.1:8000/productionorder/queue-status
curl http://127.0.0.1:8000/deliveryorder/queue-status
```

The response includes `worker_running`, `worker_phase`, `queue_size`,
`current_order_id`, `last_order_id`, `last_completed_order_id`, and `last_error`.
A stopped/failed worker is distinguished from one discovering nodes, waiting
for PLC readiness, writing an order, or waiting for start/completion/reset.
Unhandled worker exits are logged immediately. The terminal also logs when an
order is accepted and dequeued, before the first PLC readiness read.
If a worker has stopped, its POST endpoint returns `503` instead of accepting
an order into an unconsumed queue. A running worker that is retrying a connection
still accepts jobs into its in-memory queue.

Match the endpoint to the observed PLC slot: `/productionorder/` uses
`MESAuftragProduktion`; `/deliveryorder/` uses the commissioning slot. A `404`
for `/` or `/favicon.ico` is harmless; those routes are not implemented.

For the commissioning slot, expect `OPC UA child MESAuftragKommissionieren
resolved using PLC spelling MESAuftragKommisionieren`. Missing-child errors
include the parent NodeId and available child names, which distinguish a naming
mismatch from a node not exposed by the OPC UA server. A TIA Portal data-block
view shows PLC variables but does not itself prove the server's browse names.

The commissioning screenshots show `Auftragssteuerung_HMI=1` and `StatusHMI=1`
while the MES command and feedback are `0`. These are HMI-side signals; the MES
only acts on `Auftragssteuerung_MES` and `StatusMES`. For an isolated MES test,
finish or clear any HMI order through the normal HMI workflow before submitting
the API request.

Once one order finishes and resets, submit two orders with different
`order_id`/`Auftragsnummer` values. The second must start only after the first
has finished and its reset is confirmed. Then try two queue items in one order:
`Inhalt.Anzahl` must become `2`, and both slots must receive their input fields.
An empty queue or values outside the PLC integer/string limits must return `422`.

If a test fails, keep the terminal traceback and record the current command,
feedback, count, and queue item values. A start timeout means the command was
written but started/finished feedback was not observed; a reset timeout means
the PLC did not confirm idle after acknowledgement.

Current limitation: queues live only in the backend process. Restarting clears
pending jobs; failed jobs are logged and removed, without an API status or
automatic retry. Do not interpret `202` as a durable ERP acknowledgement.

## Local regression tests

```bash
cd backend
python3 -m pytest -q
```

Tests exercise the current node names, both array browse layouts, validation,
delayed feedback, completion/reset timeouts, and two successive jobs through
both workers with a simulated PLC. They do not start physical production.
