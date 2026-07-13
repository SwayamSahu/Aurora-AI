"""Video-generation model catalog — the ONE source of truth for which models
the Studio offers, and what each one can do.

A model is just data: an id, the provider that serves it, and its capability
envelope (resolution tier, duration range, image-to-video support). The
frontend renders the model picker from this catalog (via `GET /generation/
models`), and the generation pipeline clamps each request to the chosen
model's envelope (`clamp_video_params`).

Two kinds of models live here:

  * **local**   — open-weight models that actually run on our own GPU box
                  (the CUDA backend): LTX-Video, CogVideoX, Wan. On the Mac
                  these route through the mock generator like everything else.
  * **api**     — closed, hosted models reachable only through a provider (or
                  aggregator) API: Kling, Veo, Seedance, Grok, … These have no
                  public weights and cannot be self-hosted. Today they are
                  *simulated* by the mock generator so the whole multi-model
                  UX — catalog, capability-constrained options, selection —
                  is buildable and testable with no API keys and no spend.
                  Real provider adapters swap in behind the generator
                  interface later (see the multi-model plan, Phase D).

Adding a model is a one-row change here — no schema, no migration: the job
`params["model"]` is a free string threaded end to end.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Resolution tier → concrete max dimensions. The tier label is what the UI
# shows as a badge; the dims are what the pipeline clamps to.
_TIER_DIMS: dict[str, tuple[int, int]] = {
    "720p": (1280, 720),
    "1080p": (1920, 1080),
    "4K": (3840, 2160),
}


@dataclass(frozen=True)
class ModelSpec:
    id: str
    label: str
    provider: str
    #: "local" (own GPU) or "api" (hosted third-party model)
    kind: str
    #: resolution tier label — one of _TIER_DIMS keys
    resolution: str
    min_duration: int
    max_duration: int
    default_duration: int
    supports_i2v: bool = False
    #: display badges, e.g. ["NEW", "4K", "EXCLUSIVE"]
    badges: list[str] = field(default_factory=list)
    enabled: bool = True

    @property
    def max_width(self) -> int:
        return _TIER_DIMS[self.resolution][0]

    @property
    def max_height(self) -> int:
        return _TIER_DIMS[self.resolution][1]


# --------------------------------------------------------------------------- #
# The catalog
# --------------------------------------------------------------------------- #
MODEL_CATALOG: list[ModelSpec] = [
    # -- Local, open-weight models (real on the CUDA box) ------------------- #
    ModelSpec(
        id="ltx-video",
        label="LTX-Video (fast)",
        provider="Aurora (local)",
        kind="local",
        resolution="720p",
        min_duration=2,
        max_duration=6,
        default_duration=4,
        supports_i2v=True,
    ),
    ModelSpec(
        id="cogvideox-5b",
        label="CogVideoX-5B",
        provider="Aurora (local)",
        kind="local",
        resolution="720p",
        min_duration=2,
        max_duration=6,
        default_duration=4,
    ),
    ModelSpec(
        id="wan-2.1",
        label="Wan 2.1",
        provider="Alibaba (local)",
        kind="local",
        resolution="720p",
        min_duration=2,
        max_duration=6,
        default_duration=4,
        supports_i2v=True,
    ),
    # -- Hosted, closed API models (simulated until provider adapters land) - #
    ModelSpec(
        id="seedance-2.0",
        label="Seedance 2.0",
        provider="ByteDance",
        kind="api",
        resolution="4K",
        min_duration=4,
        max_duration=15,
        default_duration=5,
        supports_i2v=True,
        badges=["4K"],
    ),
    ModelSpec(
        id="seedance-2.0-mini",
        label="Seedance 2.0 Mini",
        provider="ByteDance",
        kind="api",
        resolution="720p",
        min_duration=4,
        max_duration=15,
        default_duration=5,
        badges=["NEW", "EXCLUSIVE"],
    ),
    ModelSpec(
        id="seedance-2.0-fast",
        label="Seedance 2.0 Fast",
        provider="ByteDance",
        kind="api",
        resolution="720p",
        min_duration=4,
        max_duration=15,
        default_duration=5,
    ),
    ModelSpec(
        id="gemini-omni-flash",
        label="Gemini Omni Flash",
        provider="Google",
        kind="api",
        resolution="720p",
        min_duration=4,
        max_duration=10,
        default_duration=6,
        badges=["NEW"],
    ),
    ModelSpec(
        id="kling-3.0",
        label="Kling 3.0",
        provider="Kuaishou",
        kind="api",
        resolution="4K",
        min_duration=3,
        max_duration=15,
        default_duration=5,
        supports_i2v=True,
        badges=["4K"],
    ),
    ModelSpec(
        id="kling-3.0-turbo",
        label="Kling 3.0 Turbo",
        provider="Kuaishou",
        kind="api",
        resolution="1080p",
        min_duration=3,
        max_duration=15,
        default_duration=5,
        badges=["NEW"],
    ),
    ModelSpec(
        id="kling-3.0-motion",
        label="Kling 3.0 Motion Control",
        provider="Kuaishou",
        kind="api",
        resolution="1080p",
        min_duration=3,
        max_duration=30,
        default_duration=5,
        supports_i2v=True,
    ),
    ModelSpec(
        id="happyhorse",
        label="HappyHorse",
        provider="HappyHorse",
        kind="api",
        resolution="1080p",
        min_duration=3,
        max_duration=15,
        default_duration=5,
        badges=["NEW"],
    ),
    ModelSpec(
        id="grok-imagine",
        label="Grok Imagine",
        provider="xAI",
        kind="api",
        resolution="720p",
        min_duration=1,
        max_duration=15,
        default_duration=4,
    ),
    ModelSpec(
        id="grok-imagine-1.5",
        label="Grok Imagine 1.5",
        provider="xAI",
        kind="api",
        resolution="720p",
        min_duration=1,
        max_duration=15,
        default_duration=4,
        badges=["NEW"],
    ),
    ModelSpec(
        id="veo-3.1-lite",
        label="Google Veo 3.1 Lite",
        provider="Google",
        kind="api",
        resolution="1080p",
        min_duration=4,
        max_duration=8,
        default_duration=6,
        supports_i2v=True,
        badges=["NEW"],
    ),
    ModelSpec(
        id="wan-2.7",
        label="Wan 2.7",
        provider="Alibaba",
        kind="api",
        resolution="1080p",
        min_duration=2,
        max_duration=15,
        default_duration=5,
        badges=["NEW"],
    ),
]

_BY_ID: dict[str, ModelSpec] = {m.id: m for m in MODEL_CATALOG}

#: The model selected by default when none is specified.
DEFAULT_MODEL_ID = "ltx-video"


def get_model(model_id: str | None) -> ModelSpec | None:
    """Look up a model by id. `None`/unknown returns `None`."""
    if not model_id:
        return None
    return _BY_ID.get(model_id)


def list_models(*, enabled_only: bool = True) -> list[ModelSpec]:
    if enabled_only:
        return [m for m in MODEL_CATALOG if m.enabled]
    return list(MODEL_CATALOG)


def clamp_video_params(
    spec: ModelSpec, duration: float, width: int, height: int
) -> tuple[float, int, int]:
    """Clamp a request to the model's capability envelope.

    Duration is pinned into [min, max]; width/height are capped at the model's
    resolution tier. Real API models reject out-of-range requests; clamping
    here means the same request is always valid whichever backend serves it.
    """
    duration = min(max(duration, spec.min_duration), spec.max_duration)
    width = min(width, spec.max_width)
    height = min(height, spec.max_height)
    return duration, width, height
