"""Aggregate API router. New route modules are included here per phase."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    assets,
    audio,
    auth,
    edits,
    export,
    health,
    jobs,
    projects,
    timeline,
    users,
    ws,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(projects.router)
api_router.include_router(assets.router)
api_router.include_router(jobs.router)
api_router.include_router(edits.router)
api_router.include_router(timeline.router)
api_router.include_router(audio.router)
api_router.include_router(export.router)
api_router.include_router(ws.router)

# Phase 6+: audio/captions, export …
