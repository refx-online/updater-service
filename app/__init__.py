from __future__ import annotations

from fastapi import FastAPI

from app.routes import router as route_router

asgi_app = FastAPI(
    title="updater-service",
)

asgi_app.include_router(route_router)
