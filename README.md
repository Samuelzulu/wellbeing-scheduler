# 🧠 Hybrid Student Well-Being Scheduler

A Python-based scheduling engine that generates a balanced weekly plan for students by combining academics, wellness, and personal habits.  
The system considers courses, tasks, sleep, workouts, meals, and self-care goals to produce a healthier, more productive weekly schedule.

---

## 🚀 Tech Stack (V1)

- Python 3.11+
- Pydantic (data models & validation)
- Pytest (testing)
- Virtual environment (`venv`)

> V2 will introduce FastAPI + SQLite for persistence and a minimal UI.

---

## 📂 Project Structure

```
wellbeing-scheduler/
├─ src/
│  └─ models.py            # Event, Task, WellnessGoal, Preferences
├─ tests/
│  └─ test_models.py       # Model validation tests
└─ README.md
```

---

## ▶️ Getting Started

### 1. Create & Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate     # Mac / Linux
# .venv\Scripts\activate      # Windows
```

### 2. Install Dependencies

```bash
pip install pydantic pytest
```

### 3. Run Tests

```bash
PYTHONPATH=. python3 tests/test_models.py
```

---

## 🧩 Current Features (V1)

✔ Event model (with time validation)  
✔ Task model (priority, due date, estimation validation)  
✔ Wellness goals model (sleep, meals, workouts, self-care)  
✔ Preferences model (daily scheduling boundaries)  

These models form the core input layer for the scheduling engine.

---

## 🗺️ Roadmap

### **V1 — Rules-Based Scheduler (Core Engine)**
- Place sleep, fixed events (classes), meals, study, workouts
- Generate a 7-day schedule with time blocks
- CLI output

### **V2 — Persistence + API**
- Store data in SQLite
- FastAPI endpoints for plans and tasks
- Optional minimal UI to visualize weekly plan

### **V3 — AI Balance Mentor (Optional)**
- Give recommendations on improving schedule balance
- Explain weekly plan and suggest adjustments

---

## 👤 Author

Built by **Samuel Zulu** as a portfolio project for learning and practicing real-world software engineering skills.

---

> This is a work-in-progress version. As the engine is implemented, the README will expand with demos, screenshots, and a full architecture overview.
