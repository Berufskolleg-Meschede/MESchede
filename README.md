# MESchede
<img width="1408" height="768" alt="MESchede_logo" src="https://github.com/user-attachments/assets/9758b6bb-5531-4954-ba74-01026f9bc85c" />

A school project developed at **Berufskolleg Meschede** that implements a lightweight manufacturing execution system (MES). The application manages production orders, delivery orders, storage/inventory, and factory sites, and connects to a real PLC via OPC UA.

## Documentation

This README covers setup and the high-level architecture. For deeper reference material (data model, full API contract, OPC UA/PLC handshake details, deployment, frontend status), see the **[Project Wiki](https://github.com/Berufskolleg-Meschede/MESchede/wiki)**.

## OPC UA integration

See [the current PLC handshake and offline testing guide](docs/opc-ua-integration.md).
An example production request is saved in `backend/examples/production-order.json`.

---

## Architecture Overview

The project follows a classic **three-tier architecture**, plus a direct OPC UA link from the backend to the PLC:

```
┌──────────────────────────────────────────────────────────┐
│                        Browser                           │
│              Next.js Frontend (Port 3000)                │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTP / REST
┌───────────────────────────▼──────────────────────────────┐
│              FastAPI Backend (Port 8000)                  │
│  /storage  /plc-storage  /productionorder  /deliveryorder │
│  /orders  /settings  /analytics                            │
└──────────┬────────────────────────────────┬───────────────┘
           │ SQLAlchemy / psycopg           │ OPC UA
┌──────────▼───────────────────┐  ┌─────────▼───────────────┐
│   PostgreSQL Database         │  │   PLC (Siemens S7)       │
│        (Port 5432)            │  │  DB_MES_Schnittstelle    │
└────────────────────────────────┘  └──────────────────────────┘
```

**RabbitMQ** (running on the NAS) carries stock events in both directions. The inbound consumer reads ERP snapshots/deltas from a separately configured queue and is inactive until that queue is configured. The order worker publishes one outbound delta per good product unit confirmed at order completion: `+1` for production and `-1` for delivery.

```
┌─────────────────────┐        AMQP         ┌─────────────────────┐
│   ERP / Producer(s) │ ──────────────────► │      RabbitMQ       │
│                      │                     │ Inbound stock queue  │
└─────────────────────┘                     └──────────┬──────────┘
                                                        │ ERP → MES
                                                        ▼
                                           ┌─────────────────────────┐
                                           │   FastAPI Backend       │
                                           │  (storage_consumer)     │
                                           └─────────────────────────┘
                                                        │ MES → ERP
                                                        ▼
┌─────────────────────┐        AMQP         ┌─────────────────────┐
│   ERP / Consumer(s) │ ◄────────────────── │      RabbitMQ       │
│                      │                     │  `storage` queue     │
└─────────────────────┘                     └─────────────────────┘
```

Outbound events are stored in a PostgreSQL outbox with the confirmed order result and retried until RabbitMQ confirms delivery. The AMQP `message_id` remains stable across retries; ERP consumers should deduplicate on that ID. The outbound body contains `product_id` and `quantity_delta`.

The `/inventory` frontend page no longer reads this RabbitMQ-backed `/storage` data. It now polls `GET /plc-storage/`, which reads the housing (`LagerGehaeuse`), lid magazine (`MagazinDeckel_1`/`_2`) and high-rack (`LagerProdukte`) stock nodes directly from the PLC over OPC UA, through a dedicated single-threaded `PlcStorageGateway` (separate from the order-worker's PLC connection). The legacy `/storage` endpoints and the RabbitMQ consumer still exist and run, but currently have no frontend consumer.

Development Compose starts PostgreSQL and the backend; start the frontend separately. Production Compose uses the published images and configures the frontend proxy to the backend.

---

## Technology Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Frontend   | [Next.js](https://nextjs.org/) (React, TypeScript, Tailwind CSS) |
| Backend    | [FastAPI](https://fastapi.tiangolo.com/) (Python) |
| ORM        | [SQLModel](https://sqlmodel.tiangolo.com/) + [SQLAlchemy](https://www.sqlalchemy.org/) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/)      |
| Database   | [PostgreSQL](https://www.postgresql.org/)       |
| PLC access | [opcua](https://github.com/FreeOpcUa/python-opcua) (OPC UA client) |
| Messaging  | [RabbitMQ](https://www.rabbitmq.com/) via [pika](https://pika.readthedocs.io/) (AMQP) |
| Container  | [Docker](https://www.docker.com/) / [Docker Compose](https://docs.docker.com/compose/) |

---

## Project Structure

```
MESchede/
├── docker-compose.yaml          # Dev orchestration (db + backend)
├── docker-compose.prod.yml      # Prod orchestration (published images, Traefik)
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py              # Application entry point, router + worker wiring
│   │   ├── routers/             # API route handlers
│   │   │   ├── storage_router.py
│   │   │   ├── productionorders_router.py
│   │   │   ├── deliveryorders_router.py
│   │   │   ├── orders_router.py          # combined overview + manual review
│   │   │   ├── settings_router.py        # OPC UA node/config management
│   │   │   ├── plc_storage_router.py     # live PLC stock levels (housing/lids/high-rack)
│   │   │   └── analytics_router.py
│   │   ├── models/              # SQLModel database models + pydantic DTOs
│   │   ├── domain/               # order/run state machine (phases, transitions); lager_snapshot.py (PLC stock DTOs)
│   │   ├── repositories/        # persistence for the order pipeline
│   │   ├── services/            # business logic (dispatch, analytics, reviews, settings)
│   │   ├── workers/             # background order worker + RabbitMQ consumer
│   │   ├── clients/             # OPC UA client + PLC order gateway (live) + PLC storage gateway (live); RabbitMQ outbound publisher (currently unused)
│   │   └── db/                  # database connection and session management
│   ├── alembic/                 # database migration scripts
│   ├── tests/                   # pytest suite (unit + integration, simulated PLC)
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/                    # Next.js application
    ├── app/                     # Next.js App Router pages
    ├── components/               # shared UI components (order list, review dialog, …)
    ├── hooks/                    # React hooks (e.g. polling order snapshots)
    ├── lib/                      # API clients, formatting helpers, shared types
    ├── tests/                   # Playwright e2e tests + in-memory preview harness
    ├── public/                  # static assets
    └── Dockerfile
```

---

## API Endpoints

All endpoints below are implemented by the routers under `backend/app/routers/`. Across the order-pipeline endpoints (`/productionorder`, `/deliveryorder`, `/orders`), domain errors map to HTTP status codes consistently: **409** (conflicting/stale state, e.g. reviewing with an outdated version), **404** (order/run not found), **422** (validation error), **503** (order worker not running / database unreachable).

### Storage

| Method | Endpoint                         | Description                          |
|--------|-----------------------------------|--------------------------------------|
| GET    | `/storage/`                      | List stock for every article (articles without a stock row still appear) |
| GET    | `/storage/status`                | RabbitMQ consumer health (`configured`, `connected`, `last_error`, staleness) |
| GET    | `/storage/{item_id}`             | Get stock for a specific item        |
| POST   | `/storage/{item_id}`             | Add new stock for an item            |
| PATCH  | `/storage/{item_id}`             | Update stock for an item             |
| PATCH  | `/storage/{item_id}/{amount}`    | Add or subtract stock by amount      |

> `/storage` is fed by the inbound RabbitMQ consumer (see below) and still runs, but as of the live PLC stock feature below, no frontend page currently reads it.

### PLC storage (live stock levels)

| Method | Endpoint          | Description                          |
|--------|-------------------|---------------------------------------|
| GET    | `/plc-storage/`   | Live snapshot of housing (`LagerGehaeuse`), lid magazines (`MagazinDeckel_1`/`_2`) and high-rack (`LagerProdukte`) stock, read directly from the PLC over OPC UA; **503** if the PLC can't be reached |

This is what the frontend's `/inventory` page actually polls. The node names are configurable the same way as the order nodes — see [Settings](#settings) and the Wiki's [Konfiguration](https://github.com/Berufskolleg-Meschede/MESchede/wiki/Konfiguration) page.

### Production & delivery orders

`/productionorder` and `/deliveryorder` expose the same contract for the two order types:

| Method | Endpoint                               | Description                          |
|--------|------------------------------------------|---------------------------------------|
| GET    | `/productionorder/` · `/deliveryorder/` | Paginated, searchable, status-filterable order list |
| GET    | `/productionorder/queue-status` · `/deliveryorder/queue-status` | Worker/queue diagnostics (DB only, no PLC contact) |
| GET    | `/productionorder/{order_id}` · `/deliveryorder/{order_id}` | Order/run detail and normalized `mes_auftrag` input for admission reconciliation; includes per-unit results and refresh intervals |
| POST   | `/productionorder/` · `/deliveryorder/` | Admit an order → **202 Accepted** after commit; first admission requires a fresh valid PLC catalog and sufficient queue capacity; **503** when prerequisites are unavailable |

### Combined overview & manual review

| Method | Endpoint                               | Description                          |
|--------|------------------------------------------|---------------------------------------|
| GET    | `/orders/overview`                      | Combined production + delivery summary, dispatch state, PLC source health, active/waiting orders — stored data only |
| GET    | `/orders/input-context?order_type=production` (or `delivery`) | Read-only preparation: independent unused identifiers, local plant date/time, product catalog, source availability and slot capacity |
| POST   | `/orders/catalog/sync?order_type=production` (or `delivery`) | Read the PLC catalog and persist a complete snapshot; never submits an order or writes PLC nodes |
| POST   | `/orders/runs/{run_id}/reviews`         | Submit a manual outcome (completed/interrupted/unknown) and quantities for a run; optimistic-concurrency protected (`expected_version`) and idempotent per `request_id` |

### Manual order entry (Issue #30)

Both order pages now offer **Neuer Auftrag**, multiple product rows, separate editable business and PLC identifiers, and a summary before admission. Serials increase across all rows from an editable start number within that order. Customer number is optional; priority and parameters have editable model defaults. `ORDER_PLANT_TIMEZONE` defaults to `Europe/Berlin`; the UI submits local date/time without a timezone offset. These input timestamps do not introduce scheduling or prove a PLC start.

`202` confirms durable admission only. The UI reloads the list and offers an independently refreshed detail. Before sending, it saves the immutable attempt in session storage. After an uncertain response or reload it checks the matching detail first; only a reliable `404` allows an explicit retry of the identical input. Identical existing orders are resolved before catalog validation, so a subsequent catalog outage does not invalidate their admission. Backend validation retains the shared FIFO and review/start locks.

On October 15, 2026, the interface PDF (pages 96–97) and a read-only live browse confirmed **`DB_MES_Schnittstelle.Produktspezifikation`** (singular), six products (IDs 1–6), and 33 queue slots per order type. The reader skips catalog index 0, reads the actual ID/text and all specification fields, and measures contiguous queue slots starting at 0. `Produktspezifikationen` remains a compatibility alias.

Migration `plc_catalog_01` adds `plc_catalog_product` (ID, text, source index, specification, availability, observation time) and `plc_catalog_state` (per-type capacity and synchronization status). These mirror PLC data independently of `Article`, which requires prices the PLC does not supply. Complete snapshots are imported atomically; missing products are deactivated, historical orders retain their original input. Errors preserve the last successful data and block first admission until a successful refresh. A snapshot older than `PRODUCT_CATALOG_STALE_AFTER_S` (default 300 seconds) is also unavailable for new admission.

The backend refreshes the catalog at startup and after each `PRODUCT_CATALOG_REFRESH_INTERVAL_S` interval (default 30 seconds), using a dedicated read connection so catalog reads do not delay order handshakes. Preparation and order POSTs use the persisted catalog without their own PLC calls. **Produktdaten abgleichen** explicitly requests another sync. To import once **without starting the order worker**, run `python -m app.scripts.sync_product_catalog` from `backend/` after migration. It loads configured node names and reads the PLC, then writes only the catalog tables. Real order acceptance on the plant remains pending. See [the Spec](docs/specs/issue-30-manual-order-start.md) and [implementation status](docs/plans/issue-30-manual-order-start.md).

Browser tests use an isolated production build (`MES_NEXT_DIST_DIR=.next/issue30-tests`, webpack) against a local HTTP fixture. Normal development continues to use `.next`.

### Settings

| Method | Endpoint      | Description                          |
|--------|---------------|---------------------------------------|
| GET    | `/settings/`  | Current OPC UA node names and polling interval |
| PUT    | `/settings/`  | Update node names/interval; **409** if a target node changes while an order of that type is active |

### Analytics

| Method | Endpoint     | Description                                        |
|--------|--------------|-----------------------------------------------------|
| GET    | `/analytics/` | Historical runs, filterable by `from`/`to` date and `order_type` |

### External integration

There is no REST API exposed to or consumed from the ERP system. The MES ↔ ERP integration is asynchronous via **RabbitMQ**: confirmed production and delivery results publish relative stock changes; inbound ERP stock events use a separate queue and remain inactive until its contract and name are configured. See [RabbitMQ Integration](#rabbitmq-integration) below and the [Wiki](https://github.com/Berufskolleg-Meschede/MESchede/wiki) for the full contract.

---

## Getting Started

### Prerequisites

- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) installed

### Running with Docker Compose

1. Clone the repository:
```bash
   git clone https://github.com/Berufskolleg-Meschede/MESchede.git
   cd MESchede
```

2. Create the required environment files from the provided examples and fill in real values:
   - `backend/.env` (from `backend/.env.example`) – database URL, OPC UA endpoint/credentials, RabbitMQ URL, order worker timeouts, product-result mapping
   - `backend/.env.db` (from `backend/.env.db.example`) – PostgreSQL credentials (must match `backend/.env`)
   - `frontend/.env` (from `frontend/.env.example`, production only) – `MES_BACKEND_URL` (orders proxy) and `BACKEND_INTERNAL_URL` (settings/storage/analytics proxy)

   > `env_file` values are **not** shell-interpolated by Docker Compose: `DATABASE_URL`/`ALEMBIC_DATABASE_URL` must repeat the literal host/credentials rather than reference the `POSTGRES_*` variables.

3. Start all services:
```bash
   docker compose up --build
```

4. The services will be available at:
   - **Frontend**: http://localhost:3000 after starting it separately with `npm run dev`
   - **Backend API**: http://localhost:8000
   - **API Docs (Swagger)**: http://localhost:8000/docs
   - **Database**: localhost:5432

### Running Services Individually

**Backend (development):**
```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
fastapi dev app/main.py
```

**Frontend (development):**
```bash
cd frontend
npm install
npm run dev
```

### Deploying a release on the NAS

Pushing a version tag matching `vMAJOR.MINOR.PATCH` (optionally followed by a prerelease suffix such as `-rc.1`) or publishing a GitHub Release builds and pushes separate backend and frontend images to GHCR. Both images receive the release tag, the short commit SHA tag, and `latest`. Tags must not include build metadata (such as `+nas`) and must fit Docker's 128-character tag limit.

Set the desired release tag in the `.env` file beside `docker-compose.prod.yml` on the NAS:

```env
MES_IMAGE_TAG=v0.2.0
```

Then pull and start that exact version:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

To backfill an existing release, manually run **Build and Push Docker Images to GHCR** from the `main` branch and enter its tag in the `release_tag` input (for example, `v0.2.0`). The workflow checks out that tag's source before building. Creating a valid version tag or publishing a matching GitHub Release after this workflow is deployed starts the build automatically.

---

## RabbitMQ Integration

### Übersicht
Das MES nutzt RabbitMQ für Lagerbewegungen in beide Richtungen. Der Auftragsworker veröffentlicht bestätigte Einzelbewegungen auf der dauerhaften Ausgangsqueue `storage`: jede erfolgreich produzierte Produkteinheit als `quantity_delta: 1`, jede erfolgreich ausgelieferte Produkteinheit als `quantity_delta: -1`. Fehlgeschlagene Produkte und lediglich geplante oder manuell geschätzte Mengen werden nicht veröffentlicht. Die Ereignisse werden zusammen mit dem bestätigten PLC-Ergebnis in einer Outbox gespeichert und nach Brokerbestätigung als gesendet markiert; bei Ausfall werden sie erneut versucht. Die eingehende Richtung bleibt davon getrennt und verwendet eine eigene, mit der Lager-/ERP-Gruppe abzustimmende Queue.

RabbitMQ läuft als Docker-Container auf dem NAS und ist über folgende Ports erreichbar:

| Zweck          | Port  |
|----------------|-------|
| AMQP (Backend) | 50450 |
| Web-UI         | 50451 |

### Konfiguration
Die Verbindungsdaten werden über eine `.env`-Datei konfiguriert. Eine `.env.example` liegt im Repository:

```env
RABBITMQ_URL=amqp://<user>:<password>@<host>:<port>/
```

Die echten Zugangsdaten sind nicht im Repository — bei einem Teammitglied oder dem NAS-Admin erfragen.

### Automatische ausgehende Bestandsänderungen

Der Auftragsworker veröffentlicht eine Nachricht je bestätigter guter Produkteinheit. Für ein ausgeliefertes Produkt hat der Nachrichtenkörper folgendes Format:
```json
{
  "product_id": 42,
  "quantity_delta": -5
}
```

Bei Produktion ist `quantity_delta` `1`; bei Auslieferung ist es `-1`. Der AMQP-Header `message_id` enthält eine dauerhafte MES-Ereignis-ID. Die Outbox stellt nach Broker-Ausfällen erneut zu; Empfänger sollten deshalb `message_id` zur Deduplizierung verwenden.

### Publisher manuell verwenden

Für kontrollierte manuelle Aufrufe außerhalb des Auftragsworkers kann der Publisher direkt verwendet werden:

### Klasse direkt verwenden

```python
from app.clients.rabbitmq.base import RabbitMQClient

with RabbitMQClient() as client:
    client.publish_storage_message(product_id=1, quantity_delta=-3)
    client.publish_storage_message(product_id=2, quantity_delta=+10)
```

### Nachrichten in der Web-UI prüfen
1. Web-UI öffnen: Host und Port aus der `.env` entnehmen
2. Login mit den Zugangsdaten aus der `.env`
3. **Queues → storage → Get Messages** um Nachrichten einzusehen

### Bestandsmeldungen an das MES (Vertragsentwurf)

Der MES-Consumer liest eine separate Eingangsqueue. `storage` bleibt die vom MES beschriebene
Ausgangsqueue und darf nicht zugleich als ERP-Eingangsqueue verwendet werden. Setze
`RABBITMQ_STORAGE_INBOUND_QUEUE` erst auf die mit der Lager-/ERP-Gruppe abgestimmte Queue.

Der im Backend erwartete Vertragsentwurf ist:

```json
{
  "event_id": "eindeutige-ereignis-id",
  "event_type": "snapshot",
  "product_id": 42,
  "quantity": 12,
  "occurred_at": "2026-10-13T08:00:00Z"
}
```

`event_type` ist `snapshot` oder `delta`. Snapshots setzen `quantity`, Änderungen setzen
`quantity_delta`. Jede Nachricht enthält `occurred_at` mit Zeitzone und eine eindeutige
`event_id` (alternativ AMQP `message_id`). Änderungen werden erst nach einem Snapshot für
den Artikel angewendet; so wird ein unbekannter Bestand nicht als null behandelt. Duplikate
werden anhand der Ereignis-ID ignoriert. Diese Felder und Regeln sind noch mit der
Lager-/ERP-Gruppe zu bestätigen; ohne separate Eingangsqueue bleibt der Consumer deaktiviert.

`STORAGE_STALE_AFTER_SECONDS` steuert, wann ein lange nicht aktualisierter Bestand als veraltet
markiert wird (Vorgabewert: 3600 Sekunden; ebenfalls mit der Gruppe abzustimmen).

### Beispiel für einen generischen Queue-Consumer

```python
import pika, json, os

connection = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
channel = connection.channel()
queue_name = os.getenv("RABBITMQ_STORAGE_INBOUND_QUEUE")
if not queue_name or queue_name == "storage":
    raise RuntimeError("Eine separate Eingangsqueue für Lagerdaten konfigurieren")
channel.queue_declare(queue=queue_name, passive=True)

def callback(ch, method, properties, body):
    nachricht = json.loads(body)
    print(f"Empfangen: {nachricht}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue=queue_name, on_message_callback=callback)
channel.start_consuming()
```

---

## Design Decisions

- **FastAPI** was chosen for the backend because of its automatic OpenAPI/Swagger documentation, type-safety via Pydantic, and high performance.
- **SQLModel** combines SQLAlchemy and Pydantic, reducing boilerplate for model definitions.
- **Alembic** handles database schema migrations in a controlled and versioned way.
- **Next.js** provides server-side rendering capabilities and a strong developer experience for the frontend.
- **Docker Compose** simplifies local development and deployment by bundling all services together.
- **RabbitMQ via AMQP** was chosen over MQTT because it is the native protocol of RabbitMQ with full support for queues, routing, and guaranteed message delivery — without additional plugins or configuration.
- **Optimistic concurrency + manual review** for order runs: the PLC handshake alone cannot always prove a result (e.g. unmapped product codes, a restart mid-run), so uncertain runs are surfaced for a human review instead of silently guessing, and a review itself is version-checked so two people can't overwrite each other's decision.

---

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

This is a school project. Contributions from students at Berufskolleg Meschede are welcome. See the [Wiki's "Mitwirken" page](https://github.com/Berufskolleg-Meschede/MESchede/wiki/Mitwirken) for the branch/commit workflow, and please open an issue or pull request for any improvements.
