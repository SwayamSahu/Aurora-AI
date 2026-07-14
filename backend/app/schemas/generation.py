from __future__ import annotations

from pydantic import BaseModel, Field


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
    credit_cost: int


class AdminModelRead(VideoModelSpec):
    """The admin Models console's view — adds the fields only an admin needs:
    whether the model is currently offered at all, and whether its price/
    availability has been overridden from the catalog default."""

    enabled: bool
    is_overridden: bool


class AdminModelUpdate(BaseModel):
    """Partial update — omitted fields leave their current value (override or
    catalog default) untouched."""

    enabled: bool | None = None
    credit_cost: int | None = Field(default=None, gt=0)
