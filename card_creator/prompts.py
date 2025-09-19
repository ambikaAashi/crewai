"""Helpers to craft prompts for downstream card generation models."""
from __future__ import annotations

from typing import Any, Mapping, Sequence


def build_card_html_prompt(blueprint: Mapping[str, Any]) -> str:
    """Compose a rich prompt for an LLM to render the card as HTML/CSS."""

    summary = _text(blueprint.get("card_summary"))
    messaging = blueprint.get("messaging") or {}
    headline = _text(messaging.get("headline"))
    body_copy = _text(messaging.get("body"))
    closing = _text(messaging.get("closing"))

    visual_direction = blueprint.get("visual_direction") or {}
    palette = _as_list(visual_direction.get("palette"))
    typography = _text(visual_direction.get("typography"))
    layout = _text(visual_direction.get("layout"))
    background_plan = _text(visual_direction.get("background_image_plan"))

    image_assets = blueprint.get("image_assets") or {}
    must_use_images = _collect_image_urls(image_assets.get("must_use"))
    inspirational_images = _collect_image_urls(image_assets.get("pexels_options"))

    production_notes = _as_list(blueprint.get("production_notes"))
    next_questions = _as_list(blueprint.get("next_questions"))

    lines: list[str] = [
        "You are an expert HTML/CSS designer creating a single invitation or greeting card.",
        "Produce a complete <html> document with inline <style> so the design renders standalone.",
        "Do not include any JavaScript.",
    ]

    if summary:
        lines.extend(["", "Design intent:", f"- {summary}"])

    content_lines = []
    if headline:
        content_lines.append(f"Headline: {headline}")
    if body_copy:
        content_lines.append(f"Body: {body_copy}")
    if closing:
        content_lines.append(f"Closing: {closing}")
    if content_lines:
        lines.extend(["", "Card copy:"])
        lines.extend(f"- {item}" for item in content_lines)

    direction_lines = []
    if palette:
        direction_lines.append("Palette:")
        direction_lines.extend(f"  - {color}" for color in palette)
    if typography:
        direction_lines.append(f"Typography: {typography}")
    if layout:
        direction_lines.append(f"Layout guidance: {layout}")
    if background_plan:
        direction_lines.append(f"Background plan: {background_plan}")
    if direction_lines:
        lines.extend(["", "Visual direction:"])
        lines.extend(f"- {item}" for item in direction_lines)

    imagery_lines = []
    if must_use_images:
        imagery_lines.append("Embed these user-provided images as hero/background assets:")
        imagery_lines.extend(f"  - {url}" for url in must_use_images)
    if inspirational_images:
        imagery_lines.append("Optionally reference these Pexels inspirations for mood:")
        imagery_lines.extend(f"  - {url}" for url in inspirational_images)
    if imagery_lines:
        lines.extend(["", "Imagery cues:"])
        lines.extend(f"- {item}" for item in imagery_lines)

    if production_notes:
        lines.extend(["", "Production notes (honour in layout decisions):"])
        lines.extend(f"- {note}" for note in production_notes)

    if next_questions:
        lines.extend(["", "Open questions from the brief (avoid guessing details):"])
        lines.extend(f"- {question}" for question in next_questions)

    lines.extend(
        [
            "",
            "Accessibility and formatting requirements:",
            "- Make text readable with sufficient contrast.",
            "- Use semantic HTML structure with clearly separated sections.",
            "- Keep the layout responsive for both desktop and mobile widths.",
        ]
    )

    return "\n".join(lines).strip()


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = _text(value)
    if "\n" in text:
        return [line.strip() for line in text.splitlines() if line.strip()]
    if "," in text:
        return [segment.strip() for segment in text.split(",") if segment.strip()]
    return [text] if text else []


def _collect_image_urls(candidate: Any) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    def _append(url: str | None) -> None:
        if url and url not in seen:
            urls.append(url)
            seen.add(url)

    if candidate is None:
        return urls

    if isinstance(candidate, str):
        _append(_normalise_url(candidate))
        return urls

    if isinstance(candidate, Mapping):
        for key in ("image_url", "url", "src"):
            value = candidate.get(key)
            if isinstance(value, str):
                _append(_normalise_url(value))
        return urls

    if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes, bytearray)):
        for item in candidate:
            for url in _collect_image_urls(item):
                _append(url)
        return urls

    _append(_normalise_url(str(candidate)))
    return urls


def _normalise_url(value: str) -> str | None:
    stripped = value.strip()
    if not stripped:
        return None
    collapsed = "".join(stripped.split())
    return collapsed or None


__all__ = ["build_card_html_prompt"]
