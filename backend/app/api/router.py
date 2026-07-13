"""Aggregate API router. New route modules are included here per phase."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import (
    admin,
    admin_analytics,
    admin_audit,
    admin_blog,
    admin_dmca,
    admin_ledger,
    admin_reports,
    admin_system,
    admin_users,
    assets,
    audio,
    auth,
    blog,
    commerce,
    detect,
    dmca,
    edits,
    export,
    generation,
    health,
    jobs,
    listings,
    marketplace,
    projects,
    reports,
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
api_router.include_router(generation.router)
api_router.include_router(edits.router)
api_router.include_router(detect.router)
api_router.include_router(blog.router)
api_router.include_router(marketplace.router)
api_router.include_router(listings.router)
api_router.include_router(commerce.router)
api_router.include_router(reports.router)
api_router.include_router(dmca.router)
api_router.include_router(admin.router)
api_router.include_router(admin_blog.router)
api_router.include_router(admin_users.router)
api_router.include_router(admin_ledger.router)
api_router.include_router(admin_analytics.router)
api_router.include_router(admin_reports.router)
api_router.include_router(admin_dmca.router)
api_router.include_router(admin_system.router)
api_router.include_router(admin_audit.router)
api_router.include_router(timeline.router)
api_router.include_router(audio.router)
api_router.include_router(export.router)
api_router.include_router(ws.router)

# Phase 6+: audio/captions, export …
