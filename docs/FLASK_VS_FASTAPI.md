# Flask vs FastAPI — Comparison

Based on building the same Task Management API twice.

## Routing

| | Flask | FastAPI |
|---|---|---|
| Mechanism | Blueprints + `@bp.get/post/...` decorators | `APIRouter` + `@router.get/post/...` decorators |
| Path params | `<int:task_id>` converters | Python type hints (`task_id: int`) |
| Query params | Read manually from `request.args` | Declared as typed function parameters, auto-parsed and validated |

FastAPI's function-signature-as-contract approach removes a whole class of
manual parsing/casting code that Flask requires.

## Validation

| | Flask | FastAPI |
|---|---|---|
| Library | Marshmallow (chosen explicitly for this project) | Pydantic (built in) |
| Where it runs | Explicitly called in the route (`Schema().load(...)`) | Automatic, driven by type hints, before the route body runs |
| Error format | Manually caught `ValidationError`, mapped to a `422` response | Automatic `422` with a structured error body |

FastAPI's validation is less code because it's wired into the framework;
Flask requires an explicit call and explicit error handling per route,
which is more verbose but also more visible/controllable.

## Dependency Management

| | Flask | FastAPI |
|---|---|---|
| Pattern | Manual instantiation (e.g. `service = TaskService()` at module scope) or simple constructor injection | Native `Depends()` system; a full dependency graph (DB session → service → route) resolved automatically per request |
| DB session lifecycle | `Flask-SQLAlchemy`'s scoped session, tied to the app context | `Depends(get_db)` yields a session and guarantees cleanup via generator teardown |
| Swapping implementations (e.g. in tests) | Manual monkeypatching / constructing services directly in tests | `app.dependency_overrides[...]` — a first-class override mechanism |

FastAPI's dependency injection is a genuine framework feature; Flask's
"dependency management" here is really just disciplined manual wiring.

## Request Handling

| | Flask | FastAPI |
|---|---|---|
| Request body | `request.get_json()` | Declared as a Pydantic model parameter |
| Response shape | Manually built with `jsonify()` | `response_model` enforces and documents the output shape |
| OpenAPI docs | Not automatic (would need `flask-smorest`/`apispec`) | Automatic, generated from type hints (`/docs`) |

## Sync vs Async Support

| | Flask | FastAPI |
|---|---|---|
| Native async | No native async view support in this WSGI setup (Flask 2+ can run async views, but the underlying WSGI server still handles one request per worker/thread) | First-class; `async def` endpoints run on an event loop, `def` endpoints run in a threadpool automatically |
| DB driver | Synchronous SQLAlchemy engine | Async SQLAlchemy engine (`aiosqlite`) with `await` throughout the service layer |
| Demonstrated in this project | Report generation is synchronous only (`time.sleep`) | Report generation implemented **both ways**: `time.sleep` (blocking, threadpooled) and `asyncio.sleep` (non-blocking) — see `/api/reports/sync/...` vs `/api/reports/async/...` |

**Observed difference:** hitting the sync report endpoint concurrently
from multiple clients serializes on worker/thread availability, while the
async endpoint lets the event loop interleave other work (e.g. health
checks, other requests) while the "expensive" `await asyncio.sleep(1.5)`
is in flight. In a real deployment this matters most for I/O-bound work
(external API calls, DB queries under load) — for pure CPU-bound work,
async brings no benefit without an added process/thread pool.

## Background Tasks

| | Flask | FastAPI |
|---|---|---|
| Built-in primitive | None — implemented here with a `ThreadPoolExecutor` | `BackgroundTasks`, injected into the route, runs after the response is sent |
| Production equivalent | Celery / RQ | Celery / RQ, or native `async` task if I/O-bound |

## Developer Experience

- **Flask**: minimal, unopinionated, very explicit — every validation call,
  every response shape, every dependency is written out. This gives full
  control but more boilerplate and more room for inconsistency across a
  larger codebase.
- **FastAPI**: more "batteries included" for API-specific concerns —
  validation, serialization, dependency injection, and interactive docs
  come for free from type hints. The tradeoff is a steeper reliance on
  Pydantic/typing conventions, and async code requires the whole stack
  (DB driver, session handling) to be async-aware, which raises the
  learning curve for teams new to async Python.

## Summary

Both frameworks produced a comparable, fully working REST API here. FastAPI
required noticeably less code for validation, response typing, and DI, and
adds free interactive API docs. Flask's advantage is its simplicity and
flexibility — nothing happens "magically," which some teams prefer for
debuggability and onboarding.
