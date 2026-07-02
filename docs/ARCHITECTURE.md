# Architecture Documentation

## System Architecture

Both implementations follow the same layered architecture so the two
frameworks can be compared fairly:

```
Client
  │
  ▼
Routes / Routers   (HTTP concerns: parsing, status codes, response shape)
  │
  ▼
Validation Layer    (Marshmallow in Flask, Pydantic in FastAPI)
  │
  ▼
Services            (business logic, transactions, orchestration)
  │
  ▼
Models / Database    (SQLAlchemy ORM, PostgreSQL-compatible / SQLite for dev)
```

Each layer only talks to the layer directly below it:

- **Routes/Routers** never touch the database directly — they call a service.
- **Services** never build HTTP responses — they return plain data/model
  objects or raise `ValueError` for business-rule violations, which the
  route layer translates into the right status code.
- **Models** are pure SQLAlchemy declarative classes with relationships
  and constraints; they know nothing about HTTP or validation.

```
flask-app/app/
├── config.py         # environment-based configuration
├── extensions.py      # shared SQLAlchemy() instance
├── models/            # SQLAlchemy ORM models
├── schemas/            # Marshmallow validation schemas
├── services/            # business logic + transactions
├── routes/                # Flask blueprints
└── utils/                   # logging, pagination, responses, background runner

fastapi-app/app/
├── config.py          # pydantic-settings configuration
├── database.py         # async engine, session factory, Base
├── models/              # SQLAlchemy ORM models (async-compatible)
├── schemas/               # Pydantic request/response models
├── services/                # business logic + transactions (async)
├── routers/                   # FastAPI routers
├── dependencies.py               # Depends()-based DI (DB session, auth, current user)
└── utils/                          # logging, pagination
```

## Request Flow

**Example: `POST /api/tasks`**

1. Route/router receives the JSON body.
2. Validation layer parses and validates it (Marshmallow `.load()` in
   Flask; FastAPI does this automatically from the Pydantic type hint
   before the endpoint body even runs).
3. The route calls `TaskService.create_task(data)`.
4. The service checks the referenced `project_id` exists, constructs a
   `Task`, and commits it in a transaction.
5. On success, a background task is scheduled to write an audit-log entry
   (Flask: a thread-pool submission; FastAPI: `BackgroundTasks`).
6. The route wraps the created task in a consistent response envelope
   (`{success, message, data, meta}`) and returns `201 Created`.
7. If validation fails → `422`; if a referenced entity is missing → `400`;
   if the resource itself isn't found → `404`; unhandled exceptions → `500`
   via a global error handler that also logs the exception.

## Design Decisions

- **Consistent response envelope** (`success`, `message`, `data`, `meta`)
  across both frameworks so API consumers don't need per-framework logic.
- **Services return domain objects/raise exceptions, not HTTP responses** —
  keeps business logic framework-agnostic and independently testable.
- **SQLite for local dev/tests, swappable via `DATABASE_URL`** — both
  configs read the connection string from the environment so switching to
  Postgres in production is a one-line change, no code change.
- **Background tasks kept lightweight** — a real system would use Celery/RQ
  (Flask) or an async task queue (FastAPI); here a `ThreadPoolExecutor` and
  `BackgroundTasks` respectively demonstrate the *pattern* without adding
  infrastructure dependencies to the assessment.
- **Sync vs async report generation implemented side-by-side in FastAPI**
  to make the tradeoff directly observable (see `docs/FLASK_VS_FASTAPI.md`
  and `fastapi-app/app/routers/reports.py`).
