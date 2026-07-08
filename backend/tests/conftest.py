"""Shared test fixtures.

Tests run against an isolated SQLite database (file-backed, per-session) so the
full auth/persistence stack is exercised on the Mac with no Postgres needed.
Production uses Postgres via Alembic migrations.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

# Import models so all tables are registered on Base.metadata.
import app.db.models  # noqa: F401
import app.storage as storage_mod
from app.core.config import AudioBackend, settings
from app.db.base import Base
from app.db.session import get_db
from app.generators import registry as gen_registry
from app.main import app as fastapi_app


@pytest.fixture(autouse=True)
def _isolate_storage(tmp_path):
    """Point local storage at a per-test temp dir; run jobs inline."""
    settings.local_storage_dir = str(tmp_path / "media")
    # Jobs run synchronously in the request session — no Redis/worker in tests.
    settings.celery_task_always_eager = True
    # Deterministic, fast audio (no `say`/Whisper) in tests.
    settings.audio_backend = AudioBackend.MOCK
    storage_mod.get_storage.cache_clear()
    gen_registry.get_voice_generator.cache_clear()
    gen_registry.get_transcriber.cache_clear()
    yield
    storage_mod.get_storage.cache_clear()


@pytest.fixture()
def db_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session(db_engine) -> Generator[Session, None, None]:
    TestingSessionLocal = sessionmaker(
        bind=db_engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(db_session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture()
def sample_project(db_session):
    """A project owned by a fresh user — for tests that hit services directly
    (not through the HTTP client, so no auth token is needed)."""
    from app.core.security import hash_password
    from app.db.models import Project, User

    user = User(
        email="editor@example.com",
        hashed_password=hash_password("supersecret1"),
        full_name="Editor",
    )
    db_session.add(user)
    db_session.commit()
    project = Project(owner_id=user.id, name="Edit test project")
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


@pytest.fixture()
def auth_headers(client: TestClient) -> dict[str, str]:
    """Register a user and return an Authorization header for them."""
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "alice@example.com",
            "password": "supersecret1",
            "full_name": "Alice",
        },
    )
    res = client.post(
        "/api/v1/auth/login",
        data={"username": "alice@example.com", "password": "supersecret1"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
