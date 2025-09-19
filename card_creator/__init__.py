"""Card creation crew package."""

from __future__ import annotations

from .config import Settings
from .requirements import CardRequirements, RequirementManager

__all__ = [
    "Settings",
    "CardRequirements",
    "RequirementManager",
    "CardDesignCrew",
]


def __getattr__(name: str):  # pragma: no cover - simple lazy import hook
    if name == "CardDesignCrew":
        from .crew import CardDesignCrew

        return CardDesignCrew
    raise AttributeError(name)
