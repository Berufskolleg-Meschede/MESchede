# MESchede
<img width="1408" height="768" alt="MESchede_logo" src="https://github.com/user-attachments/assets/9758b6bb-5531-4954-ba74-01026f9bc85c" />

A school project developed at **Berufskolleg Meschede** that implements a lightweight manufacturing execution system (MES). The application manages production orders, delivery orders, storage/inventory, and factory sites, and integrates with an external **Azubi-ERP** system.

<<<<<<< HEAD
/order
GET to receive newest information about orders and how to execute them

## OPC UA integration

See [the current PLC handshake and offline testing guide](docs/opc-ua-integration.md).
An example production request is saved in `backend/examples/production-order.json`.
=======
---

## Architecture Overview

The project follows a classic **three-tier architecture**:

```
┌──────────────────────────────────────────────────────────┐
│                        Browser                           │
│              Next.js Frontend (Port 3000)                │
└───────────────────────────┬──────────────────────────────┘
                            │ HTTP / REST
┌───────────────────────────▼──────────────────────────────┐
│              FastAPI Backend (Port 8000)                  │
│   /sites  /storage  /productionorder  /deliveryorder     │
└───────────────────────────┬──────────────────────────────┘
                            │ SQLAlchemy / psycopg
┌───────────────────────────▼──────────────────────────────┐
│               PostgreSQL Database (Port 5432)             │
└──────────────────────────────────────────────────────────┘
```

Storage changes are published to **RabbitMQ** (running on the NAS) so external services like the ERP can consume them asynchronously:

```
┌─────────────────────┐        AMQP         ┌─────────────────────┐
│   FastAPI Backend   │ ──────────────────► │      RabbitMQ       │
│     (Producer)      │                     │   Queue: storage    │
└─────────────────────┘                     └──────────┬──────────┘
                                                       │
                                          ┌────────────▼────────────┐
                                          │    ERP / Consumer(s)    │
                                          └─────────────────────────┘
```

All three core services are orchestrated together using **Docker Compose**.

---

## Technology Stack

| Layer      | Technology                                      |
|------------|-------------------------------------------------|
| Frontend   | [Next.js](https://nextjs.org/) (React, TypeScript, Tailwind CSS) |
| Backend    | [FastAPI](https://fastapi.tiangolo.com/) (Python) |
| ORM        | [SQLModel](https://sqlmodel.tiangolo.com/) + [SQLAlchemy](https://www.sqlalchemy.org/) |
| Migrations | [Alembic](https://alembic.sqlalchemy.org/)      |
| Database   | [PostgreSQL](https://www.postgresql.org/)       |
| Container  | [Docker](https://www.docker.com/) / [Docker Compose](https://docs.docker.com/compose/) |
| Messaging  | [RabbitMQ](https://www.rabbitmq.com/) via AMQP  |

---

## Project Structure

```
MESchede/
├── docker-compose.yaml          # Orchestrates all services
├── backend/                     # FastAPI application
│   ├── app/
│   │   ├── main.py              # Application entry point
│   │   ├── routers/             # API route handlers
│   │   │   ├── sites_router.py
│   │   │   ├── storage_router.py
│   │   │   ├── productionorders_router.py
│   │   │   └── deliveryorders_router.py
│   │   ├── models/              # SQLModel database models
│   │   │   ├── machine.py
│   │   │   ├── user.py
│   │   │   └── enums.py
│   │   ├── clients/
│   │   │   └── rabbitmq/
│   │   │       └── base.py      # RabbitMQ client & publisher
│   │   ├── services/            # Business logic
│   │   └── db/                  # Database connection and session management
│   ├── alembic/                 # Database migration scripts
│   ├── Dockerfile
│   └── requirements.txt
└── frontend/                    # Next.js application
    ├── app/                     # Next.js App Router pages
    ├── lib/                     # Shared utilities
    ├── public/                  # Static assets
    └── Dockerfile
```

---

## API Endpoints

### Internal API (Backend)

| Method | Endpoint                         | Description                          |
|--------|----------------------------------|--------------------------------------|
| GET    | `/sites/`                        | List all factory sites               |
| GET    | `/storage/`                      | List entire storage inventory        |
| GET    | `/storage/{item_id}`             | Get stock for a specific item        |
| POST   | `/storage/{item_id}`             | Add new stock for an item            |
| PATCH  | `/storage/{item_id}`             | Update stock for an item             |
| PATCH  | `/storage/{item_id}/{amount}`    | Add or subtract stock by amount      |
| GET    | `/productionorder/`              | List all production orders           |
| GET    | `/productionorder/{id}`          | Get a single production order        |
| POST   | `/productionorder/`              | Create a new production order        |
| PATCH  | `/productionorder/{id}`          | Update a production order            |
| DELETE | `/productionorder/{id}`          | Delete a production order            |
| GET    | `/deliveryorder/`                | List all delivery orders             |
| GET    | `/deliveryorder/{id}`            | Get a single delivery order          |
| POST   | `/deliveryorder/`                | Create a new delivery order          |
| PATCH  | `/deliveryorder/{id}`            | Update a delivery order              |
| DELETE | `/deliveryorder/{id}`            | Delete a delivery order              |

### External API (Azubi-ERP Integration)

| Method | Endpoint     | Description                                        |
|--------|--------------|----------------------------------------------------|
| GET    | `/inventory` | Retrieve current inventory to check production readiness |
| POST   | `/inventory` | Insert new items into inventory                    |
| GET    | `/article`   | Retrieve article information                       |
| GET    | `/order`     | Retrieve newest orders and execution details       |

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

2. Create the required environment files:
   - `backend/.env` – backend environment variables (database URL, RabbitMQ URL, etc.)
   - `backend/.env.db` – PostgreSQL credentials

3. Start all services:
```bash
   docker compose up --build
```

4. The services will be available at:
   - **Frontend**: http://localhost:3000
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

---

## RabbitMQ Integration

### Übersicht
Das MES nutzt RabbitMQ als Message Broker um Lagermengen-Änderungen als Nachrichten zu publishen.
Andere Services (z.B. ERP) können diese Nachrichten unabhängig aus der Queue abholen und verarbeiten.

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

### Nachrichten publishen

```python
from app.clients.rabbitmq.base import send_storage_message

send_storage_message(product_id=42, quantity_delta=-5)
```

Jede Nachricht hat folgendes Format:
```json
{
  "product_id": 42,
  "quantity_delta": -5
}
```

`quantity_delta` ist positiv beim Einlagern und negativ beim Auslagern.

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

### Consumer hinzufügen

```python
import pika, json, os

connection = pika.BlockingConnection(pika.URLParameters(os.getenv("RABBITMQ_URL")))
channel = connection.channel()
channel.queue_declare(queue="storage", durable=True)

def callback(ch, method, properties, body):
    nachricht = json.loads(body)
    print(f"Empfangen: {nachricht}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue="storage", on_message_callback=callback)
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

---

## Contributing

This is a school project. Contributions from students at Berufskolleg Meschede are welcome. Please open an issue or pull request for any improvements.
>>>>>>> origin/main
