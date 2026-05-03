# 🧠 Hybrid Student Well-Being Scheduler

A Python-based scheduling engine that generates a balanced weekly plan for students
by combining academics, wellness, and personal habits. The system considers fixed
events, tasks, sleep, workouts, meals, and self-care goals to produce a structured
7-day schedule with scored balance reporting and rule violation checks.

---

## 🚀 Tech Stack

- Python 3.11+
- Pydantic v2 (data models & validation)
- Typer (CLI)
- Pytest (testing)

> V2 will introduce FastAPI + SQLite for persistence and a minimal UI.

---

## 📂 Project Structure
proj1/
├── src/
│   ├── models.py      # Event, Task, WellnessGoal, Preferences — Pydantic models
│   ├── engine.py      # Scheduling engine — sleep, events, meals, workouts, study
│   ├── scoring.py     # Balance scorer — rates study / wellness / free time ratio
│   ├── rules.py       # Constraint checks — late study, back-to-back blocks, free time
│   └── cli.py         # Typer CLI entry point
└── tests/
├── test_models.py      # 25 model validation tests
├── test_engine.py      # Engine unit tests (slots, sorting, placement)
└── test_integration.py # End-to-end scoring and rules tests

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
pip install pydantic typer pytest
```

### 3. Run the scheduler

```bash
PYTHONPATH=. python3 -m src.cli --score --rules
```

Available options:

| Flag | Default | Description |
|---|---|---|
| `--sleep` | 7.0 | Minimum sleep hours per day |
| `--workouts` | 3 | Workouts per week |
| `--meals` | 3 | Meals per day |
| `--self-care` | 2 | Self-care blocks per week |
| `--earliest` | 08:00 | Earliest start time |
| `--latest` | 22:00 | Latest end time |
| `--block` | 60 | Study block length (minutes) |
| `--break-mins` | 15 | Break after each study block (minutes) |
| `--score` | off | Print weekly balance score report |
| `--rules` | off | Print rule violation report |

### 4. Run tests

```bash
PYTHONPATH=. pytest tests/ -v
```

---

## 🧩 Features

- **7-day grid** starting from the current Monday
- **Sleep blocks** placed from `latest_end` for `min_sleep_hours_per_day`
- **Fixed events** placed with overlap detection
- **Meals** spaced evenly across the day window
- **Workouts** distributed across the week based on goal frequency
- **Study blocks** fill remaining slots, rotating across tasks by priority and due date, with optional breaks
- **Balance scorer** rates each day and the full week (0.0–1.0) against ideal study/wellness/free time ratios
- **Rules engine** flags late-night study, back-to-back study blocks, and days with insufficient free time

---

## 🗺️ Roadmap

### V2 — Persistence + API
- Store schedules and tasks in SQLite
- FastAPI endpoints for plans and tasks
- Minimal UI to visualise the weekly plan

### V3 — AI Balance Mentor (Optional)
- Recommendations for improving schedule balance
- Natural language explanation of the weekly plan

---

## 👤 Author

Built by **Samuel Zulu** as a portfolio project for practising real-world software engineering.