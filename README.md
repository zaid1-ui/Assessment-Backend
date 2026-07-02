# Backend Assessment — Task Management System (Flask & FastAPI)

The same Task Management API implemented twice — once in Flask, once in
FastAPI — to demonstrate backend engineering fundamentals and highlight the
differences between the two frameworks.

## Project Overview

**Domain:** Task Management System

- **Users** own **Projects**
- **Projects** contain **Tasks**
- **Tasks** are optionally assigned to a **User** and can have **Comments**

Both apps expose an equivalent REST API, backed by SQLAlchemy, with
filtering/searching/pagination, validation, transactions, sync + async
report generation, background tasks, structured logging, and tests.

```
backend-assessment/
├── flask-app/       # Flask implementation
├── fastapi-app/      # FastAPI implementation
├── docs/               # Architecture, DB design, Flask vs FastAPI comparison
└── README.md
```

See also:
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/DATABASE_DESIGN.md`](docs/DATABASE_DESIGN.md) (includes ER diagram)
- [`docs/FLASK_VS_FASTAPI.md`](docs/FLASK_VS_FASTAPI.md)

## Setup Instructions

Requires Python 3.11+.

### Flask app

```bash
cd flask-app
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

### FastAPI app

```bash
cd fastapi-app
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

## Running the Applications

### Flask

```bash
cd flask-app
python run.py
# → http://localhost:5000
```

### FastAPI

```bash
cd fastapi-app
uvicorn main:app --reload --port 8000
# → http://localhost:8000
# Interactive docs → http://localhost:8000/docs
```

Both expose a health check at `GET /health`.

## Running Tests

### Flask

```bash
cd flask-app
pytest tests/ -v
```

### FastAPI

```bash
cd fastapi-app
pytest tests/ -v
```

Both suites cover the API layer, service layer, and database layer, and
run against an isolated in-memory SQLite database (no setup required).

## API Overview

Both implementations expose the same routes:

| Method | Path | Description |
|---|---|---|
| GET/POST | `/api/users` | List / create users |
| GET/PATCH/DELETE | `/api/users/{id}` | Retrieve / update / delete a user |
| GET/POST | `/api/projects` | List / create projects |
| GET/PATCH/DELETE | `/api/projects/{id}` | Retrieve / update / delete a project |
| GET/POST | `/api/tasks` | List (filter + search + paginate) / create tasks |
| GET/PUT/PATCH/DELETE | `/api/tasks/{id}` | Retrieve / update / delete a task |
| GET | `/api/tasks/{task_id}/comments` | List comments on a task |
| POST/DELETE | `/api/comments`, `/api/comments/{id}` | Create / delete a comment |

**Task filtering, searching & pagination** (`GET /api/tasks`):
`?status=done&priority=high&project_id=1&assignee_id=2&search=login&sort=-created_at&page=1&page_size=20`

**Report generation** (time-consuming operation):
- Flask: `GET /api/reports/projects/{project_id}` (synchronous)
- FastAPI: `GET /api/reports/sync/projects/{project_id}` (synchronous)
- FastAPI: `GET /api/reports/async/projects/{project_id}` (asynchronous)

All responses share the same envelope:

```json
{ "success": true, "message": "...", "data": { ... }, "meta": { ... } }
```

## GitHub Setup (for submission)

```bash
cd backend-assessment
git init
git add .
git commit -m "Initial commit: Flask & FastAPI task management assessment"
git branch -M main
git remote add origin <YOUR_REPO_URL>
git push -u origin main

# Add supervisor as collaborator via GitHub UI:
# Repo → Settings → Collaborators → Add people
# (take a screenshot of the collaborators list as evidence)
```
