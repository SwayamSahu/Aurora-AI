"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app import __version__
from app.api.router import api_router
from app.core.config import Environment, settings

logger = logging.getLogger(__name__)

app = FastAPI(
    title=f"{settings.app_name} API",
    version=__version__,
    description="AI video generation platform — open source.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.exception_handler(Exception)
async def _global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """In production hide internal details; in dev let FastAPI re-raise for full traceback."""
    from fastapi.exceptions import (  # noqa: PLC0415
        HTTPException,
        RequestValidationError,
    )

    if isinstance(exc, HTTPException | RequestValidationError):
        raise exc
    logger.error(
        "Unhandled error on %s %s", request.method, request.url, exc_info=exc
    )
    if settings.environment == Environment.PROD:
        return JSONResponse(
            status_code=500, content={"detail": "Internal server error."}
        )
    raise exc


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {"app": settings.app_name, "version": __version__, "docs": "/docs"}
