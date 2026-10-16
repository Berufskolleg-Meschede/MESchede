# MESchede

<img width="1408" height="768" alt="MESchede logo" src="https://github.com/user-attachments/assets/9758b6bb-5531-4954-ba74-01026f9bc85c" />

MESchede is a lightweight Manufacturing Execution System developed at Berufskolleg Meschede. It manages production and delivery orders, displays live PLC inventory, records order runs and reviews, and integrates with a Siemens S7 PLC over OPC UA.

## Documentation

This README covers the application, local setup, and release deployment. The [Project Wiki](https://github.com/Berufskolleg-Meschede/MESchede/wiki) contains the architecture, API and data model, configuration, frontend, PLC integration, and operations guides. The current PLC contract and offline troubleshooting steps are in [`docs/opc-ua-integration.md`](docs/opc-ua-integration.md).

## Features

- Production and delivery order entry, validation, queueing, status tracking, and run history.
- A shared, persistent order worker with FIFO dispatch, PLC state recovery, and manual review for uncertain results.
- Product catalog synchronization from the PLC. New orders require a fresh, valid catalog snapshot and sufficient PLC queue capacity.
- Live inventory readings directly from the PLC.
- Historical run analytics and configurable OPC UA node names.
- Optional RabbitMQ stock integration: inbound stock updates use a separately configured queue; confirmed per-unit order results are published through a durable outbox.

## Architecture

```text
Browser ──HTTP──> Next.js frontend ──> FastAPI backend ──> PostgreSQL
                                            ├── OPC UA ──> Siemens S7 PLC
                                            └── AMQP ────> RabbitMQ / ERP
```

The frontend runs as a Next.js application. The backend provides the REST API, persists order state in PostgreSQL, and runs the order worker. The worker uses a database leadership lock so only one backend instance dispatches orders to the PLC at a time. Live inventory reads use a separate PLC gateway. RabbitMQ inventory ingestion and outbound order-result events are independent of the live PLC inventory page.

### Main application pages

- `/dashboard` — combined production and delivery status.
- `/production-orders` and `/delivery-orders` — order lists, manual entry, details, and run review.
- `/inventory` — live stock values read from the PLC.
- `/analytics` — historical order runs.
- `/settings` — OPC UA node names and polling interval.

The root path `/` redirects to `/dashboard`.

### API overview

The backend serves interactive OpenAPI documentation at `/docs`.

| Area | Main routes | Purpose |
|---|---|---|
| PLC inventory | `GET /plc-storage/` | Live storage snapshot from the PLC. |
| Legacy inventory | `/storage/` | Database-backed stock and inbound RabbitMQ consumer status. |
| Production and delivery | `/productionorder/`, `/deliveryorder/` | List, inspect, and admit orders; read queue diagnostics. |
| Shared order operations | `/orders/overview`, `/orders/input-context`, `/orders/catalog/sync`, `/orders/runs/{run_id}/reviews` | Dashboard data, order preparation, catalog refresh, and manual run review. |
| Settings | `GET/PUT /settings/` | Read and update configured PLC node names and polling interval. |
| Analytics | `GET /analytics/` | Historical runs with date and order-type filters. |

An HTTP `202 Accepted` from an order submission confirms that the order was durably admitted. It does not mean the PLC has started or completed the order.

## Technology

- **Frontend:** Next.js, React, TypeScript, Tailwind CSS
- **Backend:** Python, FastAPI, SQLModel / SQLAlchemy
- **Database and migrations:** PostgreSQL, Alembic
- **PLC:** OPC UA
- **Messaging:** RabbitMQ over AMQP
- **Deployment:** Docker and Docker Compose

## Repository layout

```text
backend/                 FastAPI application, worker, migrations, and tests
frontend/                Next.js application and browser tests
docs/                    Integration guides, specifications, and project docs
.github/workflows/       CI and GHCR image publishing

docker-compose.yaml      Local backend and database services
docker-compose.prod.yml  NAS deployment using published GHCR images
```

## Local development

### Requirements

- Docker and Docker Compose for the database and backend, or Python and Node.js to run them directly.
- Copy the sample environment files and set values for your environment. Never commit real credentials.

```bash
cp backend/.env.example backend/.env
cp backend/.env.db.example backend/.env.db
cp frontend/.env.example frontend/.env
```

The Compose `env_file` format does not expand references between variables. Set `DATABASE_URL` and `ALEMBIC_DATABASE_URL` with complete connection URLs that match the database credentials.

### Start the database and backend with Compose

```bash
docker compose up --build
```

The development Compose file starts PostgreSQL and the backend. Start the frontend separately:

```bash
cd frontend
npm ci
npm run dev
```

Open the frontend at <http://localhost:3000>, the backend at <http://localhost:8000>, and the API docs at <http://localhost:8000/docs>.

### Run services directly

Backend (run the database first, then from `backend/`):

```bash
pip install -r requirements.txt
alembic upgrade head
fastapi dev app/main.py
```

Frontend (from `frontend/`):

```bash
npm ci
npm run dev
```

For PLC-connected debugging, use a single backend process without auto-reload: a reload restarts the background worker. The integration guide describes offline testing and PLC handshake behavior.

## Release images and NAS deployment

Publishing a GitHub Release whose tag follows `vMAJOR.MINOR.PATCH` (optionally with a prerelease suffix such as `-rc.1`) builds and publishes two separate images to GitHub Container Registry (GHCR):

- `ghcr.io/berufskolleg-meschede/meschede-backend:<tag>`
- `ghcr.io/berufskolleg-meschede/meschede-frontend:<tag>`

Pushing a matching version tag also triggers publishing. Each publish includes the release tag, `latest`, and a `sha-<7 character commit>` tag. Pull requests do not publish images. The workflow can also be manually run from `main` with an existing release tag to build or backfill that version.

On the NAS, set `MES_IMAGE_TAG` in the environment file used alongside `docker-compose.prod.yml` to the desired version, for example:

```env
MES_IMAGE_TAG=v0.2.1
```

Then deploy that exact backend and frontend version together:

```bash
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d
```

The production Compose file routes traffic through Traefik and expects the required NAS networks and environment files to be configured. See the Wiki's [Deployment](https://github.com/Berufskolleg-Meschede/MESchede/wiki/Deployment) and [Configuration](https://github.com/Berufskolleg-Meschede/MESchede/wiki/Configuration) pages. GHCR images are the deployable release artifacts; downloading executable files from the GitHub Release assets is not required for NAS installations.

## RabbitMQ behavior

RabbitMQ is an optional ERP integration. The inbound consumer stays disabled until `RABBITMQ_STORAGE_INBOUND_QUEUE` is configured to a dedicated queue; do not use `storage` for inbound messages. The order worker publishes one stock delta for each confirmed good product unit: `+1` for production and `-1` for delivery. It stores outbound events in PostgreSQL and marks them delivered only after broker confirmation. Consumers should deduplicate using the stable AMQP `message_id` because failed deliveries are retried.

PLC result semantics must be confirmed before interpreting quantities as measured production quality. Unknown PLC product result codes are not verified measurements; review the configuration and PLC integration guide before enabling a result mapping.

## Contributing

Use feature branches and pull requests against `main`. Keep documentation in English and update the Wiki when application behavior, configuration, API contracts, or deployment changes. See the Wiki's [Contributing](https://github.com/Berufskolleg-Meschede/MESchede/wiki/Contributing) page and the repository's `Harness/AGENTS.md` for the project workflow.

## License

This project is licensed under the [MIT License](LICENSE).
