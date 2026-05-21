"""FastAPI application factory for the LocalNode dashboard."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from altinet.display.routes import router


BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    app = FastAPI(title="Altinet LocalNode Dashboard")
    app.include_router(router)
    app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
    return app
