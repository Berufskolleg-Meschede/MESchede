# Current OPC UA integration and offline testing

This describes the PLC schema shown in the October 12, 2026 photos and the
confirmed MES handshake. It supersedes the old command-only polling described
in the June integration design.

## Node changes

Both `DB_MES_Schnittstelle.MESAuftragProduktion` and the commissioning slot use
this interface. The commissioning slot default is **`MESAuftragKommissionieren`**
(two `s`), matching the corrected PLC spelling. For compatibility, the client
also accepts the former spelling `MESAuftragKommisionieren` (one `s`), while
preferring the exact configured name if both exist. No other node is used as a
fallback.

| Node | MES behavior |
| --- | --- |
| `Kopf.Auftragssteuerung_MES` | Write `1` to start; write `0` after feedback says finished. |
| `Feedback.StatusMES` | Read `0` = idle, `1` = started, `5` = finished. The client also accepts the name `Status_MES`. |
| `Kopf.Parameter0`, `Kopf.Parameter1` | Both are request fields, defaulting to `0`. Legacy request key `Parameter` is accepted as `Parameter0`. |
| `Inhalt.Anzahl` | Derived from the number of `Produktqueue` items, never supplied separately or written under `Kopf`. Reset to `0` after completed feedback `5`, before clearing the MES command. |
| `Inhalt.ProduktID` | Unused; deliberately left untouched. Each queue item has its own `ProduktID`. |
| `Inhalt.Produktqueue` | At least one item. The live server exposes numeric child names `0` through `32` inside this node. Each requested slot is resolved before writing order data. Older `Produktqueue[n]` browse names are also supported. After completion, clear and verify the five MES input fields in every exposed slot, including unused old slots. |
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

## Product catalog: single source of truth

On October 13, 2026, the team reported that `DB_MES_Schnittstelle` also
contains a `Produktspezifikationen` array with all product information.
Use `DB_MES_Schnittstelle.Produktspezifikationen` as the authoritative source
for the MES product catalog, including product selection and validation.

- Array index `0` is empty and must be skipped when reading the catalog.
  Product entries start at index `1`.
- This applies to the product specifications array; the order's
  `Produktqueue` still starts at index `0` as documented above.
- The catalog reader is not implemented yet. Before implementing it, inspect
  the actual OPC UA browse names, fields, array bounds, and product identifiers;
  do not assume that an array index equals a `ProduktID`.

## Order sequence

1. Wait for MES command `0` and MES feedback `0` (600 s timeout, allowing a
   still active previous order to finish before the next queued order).
   If a previous completed order remains latched at command `1`/feedback `5`
   after a backend restart, acknowledge it by first clearing the product queue,
   then clearing `Anzahl` and writing command `0`; confirm idle.
2. After the existing 3 s rest buffer, write the header and all requested queue
   items; write the start command `1` last.
3. Wait for feedback `1` (30 s timeout). Feedback `5` is also accepted here
   because a very short order could finish between polls.
4. Wait for feedback `5` (600 s timeout). Feedback `0` immediately after sending
   start is **not** treated as completion.
5. Immediately after observing feedback `5`, clear `ProduktID`, `Produkttext`,
   `Seriennummer`, `Sequenznummer`, and `Takt` in every exposed product queue
   slot (not only the current count). Numeric inputs become `0`, text becomes
   empty. Read back these fields; do not acknowledge a failed cleanup.
6. Write `Inhalt.Anzahl = 0`.
7. Then write `Kopf.Auftragssteuerung_MES = 0` to acknowledge completion.
   Do not require a second observation of feedback `5`: the already observed
   completion authorizes this cleanup sequence.
8. Confirm feedback, command, and `Anzahl` are all `0` (30 s timeout), then
   allow the next queued order to start.

The count-before-command reset sequence was confirmed by the teacher on
October 13, 2026. It applies to both production and commissioning. This has
been tested locally with simulated PLCs, not yet verified by a live reset.

Production uses `AuftragsArt=1`; delivery/commissioning uses `AuftragsArt=4`.
Both workers use the same handshake implementation and poll every 0.5 s.
Neither worker writes to the HMI command or any feedback field.

The backend queues whole API orders, not individual product entries. All
entries in one request are sent together with one start command; the PLC is
responsible for processing them. Cleanup happens only after feedback `5` for
that order. Splitting multi-item delivery requests into separate one-item PLC
handshakes is not implemented. Queue cleanup resets only the MES input fields;
PLC-owned slot tracking, errors, and feedback remain untouched.

The order target browse names come from the persisted settings
(`opcua_node_production_order` and `opcua_node_delivery_order`). Each worker
resolves the current configured target before processing a new order, even
when it reuses an existing connection. That target is captured for the entire
order, including reconnects and completion/reset; settings changes must not
redirect an active order. After finishing or failing, the next order uses the
current settings. The existing PLC spelling alias remains supported.

## Delivery recovery and quantity checks

Production and delivery use the same phase-aware executor. Both accept
`Feedback.StatusMES` and `Feedback.Status_MES`: `0` idle, `1` active, `5` done.
A lost OPC UA request is handled as a connection error, not as an asyncio
worker shutdown. Read phases reconnect and continue observing the current
order within the original deadline. A VS Code stop still cancels the worker.

After an uncertain write response, the executor only checks feedback; it
never automatically sends the start command again. A lost reset response is
resolved by reading back the reset field and continuing the retained reset
phase, rather than awaiting another completion. Already applied resets are
not resent. Queue cleanup followed by count `0` and command `0` only runs after observed
feedback `5`, never to force an active order to stop. Library keepalive alone is not a health guarantee;
closed idle sessions are recovered when the next order performs its reads.

Before the start command, the writer reads back `Inhalt.Anzahl` and each
requested queue item's `ProduktID` and `Seriennummer`. Mismatches prevent
starting and are logged. Unused slots are not overwritten during dispatch,
but their MES input fields are cleared after confirmed completion. A partially
completed cleanup can resume after reconnect, reading back already cleared
fields instead of rewriting them. `Inhalt.ProduktID`, HMI commands, and
PLC-owned feedback/tracking fields remain untouched.

Repeated delivery POSTs with the same `order_id` and identical normalized
payload are acknowledged with `duplicate: true`, `queued: false` without
adding a second job. Reusing an ID with a different payload returns `409`.
This protection lasts only for the current backend process; it is not a
durable ERP/exactly-once guarantee. Accepted IDs are retained even if a job
fails: do not blindly create a new ID to retry an uncertain physical order.

The team confirmed a live delivery request with one queue item and
`Anzahl=1` still unloaded all red products and remained at feedback `1`.
The team also reported feedback continuously cycling through `0`, `1`, `5`.
These PLC behaviors are **not proven fixed by the backend changes**. The PLC
commissioning logic must respect the count and requested product/serial
number, and reliably signal completed feedback `5`. Do not perform further
live deliveries until this discrepancy is resolved: a cycling feedback signal
cannot safely distinguish a real completion from an unrelated transition.

## Product catalog: single source of truth

On October 13, 2026, the team reported that `DB_MES_Schnittstelle` also
contains a `Produktspezifikationen` array with all product information.
Use `DB_MES_Schnittstelle.Produktspezifikationen` as the authoritative source
for the MES product catalog, including product selection and validation.

- Array index `0` is empty and must be skipped when reading the catalog.
  Product entries start at index `1`.
- This applies to the product specifications array; the order's
  `Produktqueue` still starts at index `0` as documented above.
- The catalog reader is not implemented yet. Before implementing it, inspect
  the actual OPC UA browse names, fields, array bounds, and product identifiers;
  do not assume that an array index equals a `ProduktID`.

## Analytics data currently confirmed

The currently documented PLC contract only confirms `StatusMES` values for ready,
started, and completed states. It does not define a result counter or a per-product
quality/result field. The MES records the times at which it observes status `1`
and status `5`; a short order first seen at status `5` has no confirmed start time.
Until the control group confirms result fields and their meaning, good, defective,
and processed quantities remain unknown. `Inhalt.Anzahl` and the requested product
queue describe the plan and must not be treated as produced output.

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
feedback `1`, feedback `5`, then empty queue inputs, count `0`, command `0` and feedback `0`. The VS Code
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

For the commissioning slot, expect the exact `MESAuftragKommissionieren` node
to resolve without an alias. If the former PLC spelling is still present, logs
may report `resolved using PLC spelling MESAuftragKommisionieren`. Missing-child errors
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

Order requests and run state are persisted in PostgreSQL. A `202` confirms
durable admission, not dispatch or completion. The shared worker reconciles
stored run state after restart instead of replaying a start blindly.

For Issue #29, a correlated `StatusMES=5` marks the order completed. Known,
explicitly mapped product failures remain in the failed count; missing or
unmapped unit results count as successful. If the PLC command was already
manually reset to `0` after a stored completion, the worker accepts the idle
state and releases the reservation without reopening a stale review.

## Local regression tests

```bash
cd backend
python3 -m pytest -q
```

Tests exercise the current node names, both array browse layouts, validation,
delayed feedback, completion/reset timeouts, and two successive jobs through
both workers with a simulated PLC. They do not start physical production.
