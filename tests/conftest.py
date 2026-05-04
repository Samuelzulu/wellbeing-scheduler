import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database.models import Base
from src.database.session import get_db
from src.api.main import create_app

# in-memory SQLite — isolated per test session, never touches scheduler.db
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session", autouse=True)
def setup_db():
    """Create all tables once for the test session."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    """Fresh DB session per test, rolled back after."""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture()
def client(db):
    """TestClient wired to the in-memory DB via dependency override."""
    app = create_app()

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c


# reusable payload factories
def task_payload(**overrides) -> dict:
    base = {
        "title": "COMP 232 Quiz",
        "estimated_minutes": 120,
        "priority": 3,
        "due_date": "2099-01-01",
    }
    return {**base, **overrides}


def event_payload(**overrides) -> dict:
    base = {
        "name": "Lecture",
        "date": "2099-06-02",
        "start_time": "09:00:00",
        "end_time": "10:00:00",
        "category": "class",
    }
    return {**base, **overrides}


def plan_payload(**overrides) -> dict:
    base = {
        "sleep": 7.0,
        "workouts": 3,
        "meals": 3,
        "self_care": 2,
        "earliest": "08:00",
        "latest": "22:00",
        "block_minutes": 60,
        "break_minutes": 15,
    }
    return {**base, **overrides}