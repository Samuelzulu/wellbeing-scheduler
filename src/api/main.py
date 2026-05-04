from fastapi import FastAPI
from ..database.session import init_db
from .routers import tasks, events, plans


def create_app() -> FastAPI:
    app = FastAPI(
        title="Student Well-Being Scheduler",
        description="Generate and persist balanced weekly schedules.",
        version="2.0.0",
    )

    @app.on_event("startup")
    def startup() -> None:
        init_db()

    app.include_router(tasks.router)
    app.include_router(events.router)
    app.include_router(plans.router)

    @app.get("/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok"}

    return app


app = create_app()