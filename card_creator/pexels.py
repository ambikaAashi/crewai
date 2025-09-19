"""Pexels API integration for fetching inspirational card backgrounds."""
from __future__ import annotations

import logging
from dataclasses import dataclass
import requests

LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class PexelsPhoto:
    """Simplified representation of a Pexels photo entry."""

    id: int
    url: str
    photographer: str
    photographer_url: str
    image_url: str
    avg_color: str | None = None


def search_backgrounds(
    api_key: str | None,
    query: str,
    *,
    per_page: int = 5,
    orientation: str = "landscape",
) -> list[PexelsPhoto]:
    """Search the Pexels API for backgrounds that match the provided query."""

    if not api_key:
        LOGGER.warning("No Pexels API key supplied; skipping image search.")
        return []

    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": api_key}
    params = {
        "query": query,
        "per_page": per_page,
        "orientation": orientation,
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as exc:
        LOGGER.error("Pexels API request failed: %s", exc)
        return []

    payload = response.json()
    photos: list[PexelsPhoto] = []
    for entry in payload.get("photos", []):
        src = entry.get("src", {})
        photos.append(
            PexelsPhoto(
                id=entry.get("id"),
                url=entry.get("url"),
                photographer=entry.get("photographer", ""),
                photographer_url=entry.get("photographer_url", ""),
                image_url=src.get("large2x") or src.get("original") or entry.get("url"),
                avg_color=entry.get("avg_color"),
            )
        )
    return photos


__all__ = ["PexelsPhoto", "search_backgrounds"]
