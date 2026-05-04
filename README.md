# 🧠 Hybrid Student Well-Being Scheduler

A Python-based scheduling engine that generates a balanced weekly plan for students
by combining academics, wellness, and personal habits. V2 adds a FastAPI REST API
and SQLite persistence on top of the V1 scheduling engine.

---

## 🚀 Tech Stack

- Python 3.11+
- Pydantic v2 (data models & validation)
- SQLAlchemy + SQLite (persistence)
- Alembic (database migrations)
- FastAPI + Uvicorn (REST API)
- Typer (CLI)
- Pytest (141 tests)

---

## 📂 Project Structure

proj1/
├── src/
│   ├── models.py          # Pydantic models — Event, Task, WellnessGoal, Preferences
│   ├── engine.py          # Scheduling engine — sleep, events, meals, workouts, study
│   ├── scoring.py         # Balance scorer — rates study / wellness / free time ratio
│   ├── rules.py           # Constraint checks — late study, back-to-back, free time
│   ├── cli.py             # Typer CLI entry point
│   ├── database/
│   │   ├── models.py      # SQLAlchemy ORM models
│   │   ├── session.py     # Session factory and DB initialisation
│   │   └── crud.py        # CRUD helpers for all entities
│   └── api/
│       ├── schemas.py     # Pydantic request/response schemas
│       ├── main.py        # FastAPI app factory
│       └── routers/
│           ├── tasks.py   # GET, POST, PATCH, DELETE /tasks
│           ├── events.py  # GET, POST, DELETE /events
│           └── plans.py   # POST /plans/generate, GET /plans, GET /plans/{id}
├── alembic/               # Database migrations
├── tests/
│   ├── conftest.py            # Shared fixtures and in-memory DB setup
│   ├── test_models.py         # 25 Pydantic model validation tests
│   ├── test_engine.py         # 30 engine unit tests
│   ├── test_integration.py    # 15 scoring and rules integration tests
│   ├── test_api_tasks.py      # 28 tasks API tests
│   ├── test_api_events.py     # 14 events API tests
│   └── test_api_plans.py      # 19 plans API tests
├── alembic.ini
├── scheduler.db           # SQLite database (auto-created on first run)
└── README.md


---

## ▶️ Getting Started

### 1. Create & activate virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate     # Mac / Linux
# .venv\Scripts\activate      # Windows
```

### 2. Install dependencies

```bash
pip install pydantic sqlalchemy alembic fastapi uvicorn httpx typer pytest
```

### 3. Run database migrations

```bash
alembic upgrade head
```

### 4. Start the API server

```bash
PYTHONPATH=. uvicorn src.api.main:app --reload
```

API is live at `http://127.0.0.1:8000`
Interactive docs at `http://127.0.0.1:8000/docs`

### 5. Or use the CLI instead

```bash
PYTHONPATH=. python3 -m src.cli --score --rules
```

### 6. Run tests

```bash
PYTHONPATH=. pytest tests/ -v
```

---

## 🌐 API Endpoints

### Tasks

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/tasks/` | Create a task |
| `GET` | `/tasks/` | List all tasks |
| `GET` | `/tasks/{id}` | Get a task by ID |
| `PATCH` | `/tasks/{id}` | Update a task |
| `DELETE` | `/tasks/{id}` | Delete a task |

### Events

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/events/` | Create a fixed event |
| `GET` | `/events/` | List all events |
| `GET` | `/events/{id}` | Get an event by ID |
| `DELETE` | `/events/{id}` | Delete an event |

### Plans

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/plans/generate` | Generate and persist a weekly plan |
| `GET` | `/plans/` | List all plans (summary, no blocks) |
| `GET` | `/plans/{id}` | Get a plan with all blocks |

### Health

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Server health check |

---

## 📋 Example Usage

```bash
# add a task
curl -X POST http://localhost:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title":"COMP 232 Quiz","estimated_minutes":120,"priority":5,"due_date":"2099-01-01"}'

# add a fixed event
curl -X POST http://localhost:8000/events/ \
  -H "Content-Type: application/json" \
  -d '{"name":"Lecture","date":"2026-05-05","start_time":"09:00:00","end_time":"10:00:00","category":"class"}'

# generate a weekly plan using all tasks and events in the DB
curl -X POST http://localhost:8000/plans/generate \
  -H "Content-Type: application/json" \
  -d '{"sleep":7.5,"workouts":4,"meals":3,"block_minutes":60,"break_minutes":15}'

# retrieve the plan
curl http://localhost:8000/plans/1
```

---

## 🧩 Features

**Scheduling engine (V1)**
- 7-day grid starting from the current Monday
- Sleep blocks placed from `latest_end` for `min_sleep_hours_per_day`
- Fixed events placed with overlap detection
- Meals spaced evenly across the day window
- Workouts distributed across the week
- Study blocks fill remaining slots, rotating across tasks by priority and due date
- Balance scorer rates each day and the full week (0.0–1.0)
- Rules engine flags late-night study, back-to-back blocks, and low free time

**API + persistence (V2)**
- Full CRUD for tasks and events via REST API
- Plans generated from live DB data and persisted with all blocks
- In-memory SQLite for isolated test runs
- Swagger UI at `/docs` for interactive exploration

---

## 🗺️ Roadmap

### V3 — AI Balance Mentor (Optional)
- Natural language explanation of the weekly plan
- Recommendations for improving schedule balance
- Conversational adjustments ("move my workouts to mornings")

---

## 👤 Author

Built by **Samuel Zulu** as a portfolio project for practising real-world software engineering.