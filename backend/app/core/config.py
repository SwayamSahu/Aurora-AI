"""Application configuration.

All settings are environment-driven so the SAME codebase runs on the Mac
(mock generators, CPU) and the NVIDIA box (CUDA generators) by changing env
vars only — no code changes. See `GENERATOR_BACKEND`.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class GeneratorBackend(str, Enum):
    """Which implementation of the AI generators to use."""

    MOCK = "mock"  # returns fixture media instantly — Mac development & tests
    REMOTE = "remote"  # calls a remote worker (e.g. the NVIDIA box over a tunnel)
    CUDA = "cuda"  # runs real models locally on an NVIDIA GPU — Phase 9


class Environment(str, Enum):
    DEV = "dev"
    TEST = "test"
    PROD = "prod"


class StorageBackend(str, Enum):
    """Where uploaded/generated media bytes live."""

    LOCAL = "local"  # local filesystem — Mac dev & tests, no MinIO needed
    MINIO = "minio"  # S3-compatible object storage (docker compose / prod)


class AudioBackend(str, Enum):
    """TTS + transcription backend (CPU-real on Mac and Linux)."""

    REAL = "real"  # TTS engine (see TtsEngine) + faster-whisper
    MOCK = "mock"  # fixture audio + canned segments (tests)


class TtsEngine(str, Enum):
    """Which TTS engine to use when audio_backend=real.

    auto    -> macOS `say` if on Darwin, else `espeak-ng` if available
    say     -> force macOS `say`
    espeak  -> force Linux/macOS `espeak-ng`
    kokoro  -> torch-based Kokoro 82M (best quality; needs tts-kokoro deps)
    mock    -> always return fixture audio (useful in dev without any TTS)
    """

    AUTO = "auto"
    SAY = "say"
    ESPEAK = "espeak"
    KOKORO = "kokoro"
    MOCK = "mock"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # --- App ---
    app_name: str = "Aurora"
    environment: Environment = Environment.DEV
    debug: bool = True
    api_v1_prefix: str = "/api/v1"

    # --- Security (used from Phase 1) ---
    secret_key: str = "dev-insecure-change-me"
    access_token_expire_minutes: int = 60 * 24

    # --- CORS ---
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # --- Database ---
    database_url: str = "postgresql+psycopg2://aurora:aurora@localhost:5432/aurora"

    # --- Redis / Celery ---
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"
    # When True, jobs run synchronously in-process (no Redis/worker needed).
    # Used for standalone Mac dev and tests; the docker stack runs a real worker.
    celery_task_always_eager: bool = False

    # --- Object storage ---
    storage_backend: StorageBackend = StorageBackend.LOCAL
    # Local filesystem backend (Mac dev/tests).
    local_storage_dir: str = "./data/media"
    # MinIO / S3 backend.
    s3_endpoint: str = "localhost:9000"
    s3_access_key: str = "aurora"
    s3_secret_key: str = "aurora-secret"
    s3_bucket: str = "aurora-media"
    s3_secure: bool = False

    # --- Generators (the swappable contract) ---
    generator_backend: GeneratorBackend = GeneratorBackend.MOCK
    # URL of the remote worker when generator_backend == remote
    remote_generator_url: str | None = None

    # Audio (TTS + transcription) is CPU-real on BOTH Mac and the GPU box, so it
    # is controlled separately from the GPU backend.  Tests force "mock".
    audio_backend: AudioBackend = AudioBackend.REAL

    # Which TTS engine to use when audio_backend=real.
    # auto  = platform-based (say on macOS, espeak-ng on Linux)
    # kokoro = torch-based Kokoro 82M (best quality; ~600MB-1GB first run)
    tts_engine: TtsEngine = TtsEngine.AUTO

    # Kokoro-specific settings (only read when tts_engine=kokoro).
    # lang: "a"=American English, "b"=British, "e"=Spanish, "f"=French, etc.
    kokoro_lang: str = "a"
    kokoro_default_voice: str = "af_heart"

    # faster-whisper model size for transcription
    whisper_model: str = "base"

    # --- Marketplace ---
    # Cut of each sale's credits the platform keeps; the rest goes to the
    # seller's wallet. No platform wallet exists in v1 — the fee amount is
    # simply not credited anywhere (retained implicitly).
    marketplace_platform_fee: float = 0.10

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug(cls, value: object) -> object:
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"release", "prod", "production"}:
                return False
            if normalized in {"dev", "development"}:
                return True
        return value

    @property
    def is_gpu_backend(self) -> bool:
        return self.generator_backend == GeneratorBackend.CUDA


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
