# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

MESchede is a lightweight Manufacturing Execution System (MES) built as a school project at Berufskolleg Meschede. It manages production orders, delivery orders, and storage inventory, and communicates with an external Azubi-ERP system and OPC-UA capable factory machines.

## Commands

### Full Stack (Docker)
```bash
docker compose up --build   # starts db + backend only (frontend runs separately)
```

### Backend
```bash
cd backend
fastapi dev app/main.py     # development server on port 8000
alembic upgrade head        # apply migrations
alembic revision --autogenerate -m "description"  # generate new migration
```

### Frontend
```bash
cd frontend
npm run dev     # development server on port 3000
npm run build
npx eslint      # lint
```

### Environment Files (required before running)
- `backend/.env` — must contain `DATABASE_URL` (async postgres URL, e.g. `postgresql+asyncpg://...`)
- `backend/.env.db` — PostgreSQL credentials: `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`

## Architecture

```
Next.js Frontend (port 3000)
        ↓ HTTP/REST
FastAPI Backend (port 8000)
        ↓ SQLAlchemy async
PostgreSQL (port 5432)
```

The backend also has an outbound integration with an Azubi-ERP HTTP API and an abstract OPC-UA client (`app/clients/opcua/base.py`) for communicating with factory machines.

## Backend Patterns

**Model convention**: Every entity uses a Base + table class split:
- `XxxBase(SQLModel)` — shared fields, used as request/response schema
- `Xxx(XxxBase, table=True)` — adds `id` primary key and relationships, maps to DB table

**Async everywhere**: All routers use `async def` and `Depends(get_session)` from `app/db/db.py`, which yields an `AsyncSession`. `app/db/session.py` is a sync session used only by Alembic.

**Router pattern**: Each resource has its own router in `app/routers/`, registered in `app/main.py`. Routes follow REST conventions with `Base` models for input and full models for output.

**Enums** (`app/models/enums.py`): `OrderStatus` (pending → in_progress → completed/error), `MachineStatus` (offline/online).

## Frontend Patterns

Uses Next.js App Router (`frontend/app/`). UI components use shadcn/ui (`components.json`), Tailwind CSS v4, and `lucide-react` icons. Shared class utilities are in `frontend/lib/utils.ts`.

## API Docs

Swagger UI is available at `http://localhost:8000/docs` when the backend is running.
