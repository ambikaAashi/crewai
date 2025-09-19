"""Utilities to transform card blueprints into shareable HTML previews."""
from __future__ import annotations

from html import escape
import re
from typing import Any, Mapping, Sequence


_HEX_COLOR_PATTERN = re.compile(r"^#(?:[0-9a-fA-F]{3}){1,2}$")


def blueprint_to_html(
    blueprint: Mapping[str, Any],
) -> str:
    """Render a simple HTML preview for a generated card blueprint.

    The HTML aims to be a faithful, human readable representation so that
    end-users can quickly preview the copy, core imagery and production
    details suggested by the crew. The markup purposefully avoids any
    JavaScript to make it easy to copy into a static ``.html`` file.
    """

    summary = _text(blueprint.get("card_summary"))
    messaging = blueprint.get("messaging") or {}
    headline = _text(messaging.get("headline")) or summary or "Your Card Headline"
    body_copy = _text(messaging.get("body"))
    closing = _text(messaging.get("closing"))

    visual_direction = blueprint.get("visual_direction") or {}
    palette = visual_direction.get("palette")
    typography = _text(visual_direction.get("typography"))
    layout = _text(visual_direction.get("layout"))
    background_plan = _text(visual_direction.get("background_image_plan"))

    image_assets = blueprint.get("image_assets") or {}
    background_image = _select_background_image(image_assets)

    production_notes = _as_list(blueprint.get("production_notes"))
    next_questions = _as_list(blueprint.get("next_questions"))

    palette_items = _palette_items(palette)
    palette_markup = "".join(_render_palette_item(item) for item in palette_items) or (
        f"<li>{escape(_text(palette) or 'Not specified')}</li>"
    )

    production_markup = (
        "".join(f"<li>{escape(note)}</li>" for note in production_notes)
        or "<li>No production notes provided.</li>"
    )
    questions_markup = (
        "".join(f"<li>{escape(question)}</li>" for question in next_questions)
        or "<li>No outstanding questions.</li>"
    )

    meta_sections = []
    if typography:
        meta_sections.append(
            f"<li><strong>Typography:</strong> {escape(typography)}</li>"
        )
    if layout:
        meta_sections.append(f"<li><strong>Layout:</strong> {escape(layout)}</li>")
    if background_plan:
        meta_sections.append(
            f"<li><strong>Background Plan:</strong> {escape(background_plan)}</li>"
        )

    background_style = ""
    if background_image:
        safe_url = background_image.replace("\"", "%22").replace("'", "%27")
        background_style = f" style=\"background-image: url('{safe_url}');\""

    overlay_opacity = "1" if background_image else "0"
    text_color = "#f9fafb" if background_image else "#1f2933"
    summary_block = (
        f'<div class=\"card__summary\">{escape(summary)}</div>' if summary else ""
    )
    body_block = (
        f'<p class=\"card__body\">{escape(body_copy)}</p>' if body_copy else ""
    )
    closing_block = (
        f'<p class=\"card__closing\">{escape(closing)}</p>' if closing else ""
    )
    meta_block = (
        f"<ul class=\"meta\">{''.join(meta_sections)}</ul>" if meta_sections else ""
    )

    return f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <title>Card Preview</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: 'Helvetica Neue', Arial, sans-serif;
    }}
    body {{
      margin: 0;
      padding: 2rem;
      background: #f3f4f6;
      color: #1f2933;
    }}
    .preview {{
      max-width: 960px;
      margin: 0 auto;
      display: grid;
      gap: 2rem;
    }}
    @media (min-width: 900px) {{
      .preview {{
        grid-template-columns: 2fr 1fr;
        align-items: start;
      }}
    }}
    .card {{
      position: relative;
      border-radius: 20px;
      overflow: hidden;
      box-shadow: 0 20px 40px rgba(15, 23, 42, 0.18);
      background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(255,255,255,0.85));
      backdrop-filter: blur(4px);
      min-height: 340px;
      display: flex;
      align-items: stretch;
    }}
    .card::before {{
      content: "";
      position: absolute;
      inset: 0;
      background: rgba(17, 24, 39, 0.35);
      mix-blend-mode: multiply;
      opacity: {overlay_opacity};
      transition: opacity 0.3s ease;
      pointer-events: none;
    }}
    .card__hero {{
      background-size: cover;
      background-position: center;
      flex: 1;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 3rem 2.5rem;
      position: relative;
    }}
    .card__hero::after {{
      content: "";
      position: absolute;
      inset: 0;
      background: rgba(17, 24, 39, 0.55);
      opacity: {overlay_opacity};
    }}
    .card__content {{
      position: relative;
      z-index: 1;
      width: 100%;
      color: {text_color};
      text-align: center;
    }}
    .card__summary {{
      text-transform: uppercase;
      letter-spacing: 0.3em;
      font-size: 0.75rem;
      margin-bottom: 1rem;
      opacity: 0.8;
    }}
    .card__headline {{
      font-size: clamp(2.2rem, 3vw + 1.5rem, 3.2rem);
      margin: 0 0 1.5rem 0;
      line-height: 1.1;
    }}
    .card__body {{
      font-size: 1.05rem;
      line-height: 1.6;
      margin: 0 0 2rem 0;
      white-space: pre-line;
    }}
    .card__closing {{
      font-size: 1rem;
      font-weight: 600;
      margin: 0;
    }}
    .details {{
      background: white;
      border-radius: 16px;
      padding: 1.5rem;
      box-shadow: 0 12px 24px rgba(15, 23, 42, 0.08);
    }}
    .details h2 {{
      margin-top: 0;
      font-size: 1.25rem;
    }}
    .palette {{
      list-style: none;
      padding: 0;
      margin: 0;
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
    }}
    .palette li {{
      display: flex;
      align-items: center;
      gap: 0.5rem;
      font-size: 0.95rem;
    }}
    .palette__chip {{
      width: 28px;
      height: 28px;
      border-radius: 50%;
      border: 1px solid rgba(15,23,42,0.15);
      background: #e5e7eb;
      box-shadow: inset 0 1px 2px rgba(255,255,255,0.8);
    }}
    .details ul {{
      padding-left: 1.2rem;
    }}
    .details li {{
      margin-bottom: 0.5rem;
    }}
    .meta {{
      list-style: none;
      padding: 0;
      margin: 1rem 0 0 0;
      font-size: 0.95rem;
    }}
    .meta li {{
      margin-bottom: 0.5rem;
    }}
    footer {{
      margin-top: 2rem;
      font-size: 0.85rem;
      color: #4b5563;
      text-align: center;
    }}
  </style>
</head>
<body>
  <div class=\"preview\">
    <div class=\"card\">
      <div class=\"card__hero\"{background_style}>
        <div class=\"card__content\">
          {summary_block}
          <h1 class=\"card__headline\">{escape(headline)}</h1>
          {body_block}
          {closing_block}
        </div>
      </div>
    </div>
    <aside class=\"details\">
      <h2>Design Direction</h2>
      <h3>Palette</h3>
      <ul class=\"palette\">{palette_markup}</ul>
      {meta_block}
      <h3>Production Notes</h3>
      <ul>{production_markup}</ul>
      <h3>Open Questions</h3>
      <ul>{questions_markup}</ul>
    </aside>
  </div>
  <footer>Generated from your card blueprint — feel free to customise the HTML further.</footer>
</body>
</html>"""


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


def _palette_items(value: Any) -> list[tuple[str, str | None]]:
    items: list[tuple[str, str | None]] = []
    for entry in _as_list(value):
        color_code = entry if _HEX_COLOR_PATTERN.match(entry) else None
        items.append((entry, color_code))
    return items


def _render_palette_item(item: tuple[str, str | None]) -> str:
    label, color = item
    chip_style = f" style=\"background:{color};\"" if color else ""
    return f"<li><span class=\"palette__chip\"{chip_style}></span><span>{escape(label)}</span></li>"


def _select_background_image(image_assets: Mapping[str, Any]) -> str | None:
    for key in ("must_use", "pexels_options"):
        candidate = image_assets.get(key)
        url = _first_image_url(candidate)
        if url:
            return url
    return None


def _first_image_url(candidate: Any) -> str | None:
    if candidate is None:
        return None
    if isinstance(candidate, str):
        return candidate.strip() or None
    if isinstance(candidate, Mapping):
        for key in ("image_url", "url", "src"):
            value = candidate.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return None
    if isinstance(candidate, Sequence) and not isinstance(candidate, (str, bytes, bytearray)):
        for item in candidate:
            url = _first_image_url(item)
            if url:
                return url
    return None


__all__ = ["blueprint_to_html"]
