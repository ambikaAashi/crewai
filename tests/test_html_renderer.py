from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from card_creator.html_renderer import blueprint_to_html


def test_blueprint_to_html_includes_core_content() -> None:
    blueprint = {
        "card_summary": "Elegant wedding invitation",
        "messaging": {
            "headline": "Celebrate with us",
            "body": "Join us for a joyful union",
            "closing": "With love, A&B",
        },
        "visual_direction": {
            "palette": ["#FADADD", "#C5A3FF"],
            "typography": "Script headline with serif body",
            "layout": "Centered folded layout",
            "background_image_plan": "Watercolour wash backdrop",
        },
        "image_assets": {
            "must_use": ["https://example.com/custom.jpg"],
            "pexels_options": ["https://images.example/alt.jpg"],
        },
        "production_notes": ["Print on 300gsm cotton paper", "Gold foil accents"],
        "next_questions": ["Confirm RSVP deadline"],
    }

    html = blueprint_to_html(blueprint)

    assert "<!DOCTYPE html>" in html
    assert "Celebrate with us" in html
    assert "Join us for a joyful union" in html
    # closing text should be HTML escaped because of ampersand
    assert "With love, A&amp;B" in html
    assert "https://example.com/custom.jpg" in html
    assert "#FADADD" in html
    assert "Typography:" in html
    assert "Gold foil accents" in html
    assert "Confirm RSVP deadline" in html


def test_blueprint_to_html_handles_missing_sections() -> None:
    blueprint = {
        "messaging": {"headline": "Simple Hello"},
        "image_assets": {},
    }

    html = blueprint_to_html(blueprint)

    assert "Simple Hello" in html
    assert "No production notes provided" in html
    assert "No outstanding questions" in html
