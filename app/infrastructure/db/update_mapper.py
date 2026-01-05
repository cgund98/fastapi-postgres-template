"""Utility for building update values from dataclasses."""

from dataclasses import asdict
from typing import Any

from app.domain.types import UNSET


def build_update_values(update: Any) -> dict[str, Any]:
    """Build update values dict from a dataclass, filtering out unset values."""
    return {key: value for key, value in asdict(update).items() if value is not UNSET}
