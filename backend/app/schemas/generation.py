from __future__ import annotations

from pydantic import BaseModel


class VideoModelSpec(BaseModel):
    """A selectable video-generation model, as shown in the Studio picker.

    Mirrors `app.generators.model_catalog.ModelSpec` (capability envelope +
    display metadata). The frontend renders the model gallery from a list of
    these and constrains its duration/resolution options accordingly.
    """

    id: str
    label: str
    provider: str
    kind: str
    resolution: str
    max_width: int
    max_height: int
    min_duration: int
    max_duration: int
    default_duration: int
    supports_i2v: bool
    badges: list[str]
