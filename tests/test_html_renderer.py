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


def test_blueprint_to_html_cleans_image_urls() -> None:
    messy_url = "https://example.com/assets/IMG-20240416-WA000\n9-e1747995653537-300x300.jpg"
    blueprint = {
        "image_assets": {
            "must_use": [messy_url],
            "pexels_options": [
                {"image_url": " https://images.example/pexels-photo-3873490.jpeg?auto=c\nompress "}
            ],
        }
    }

    html = blueprint_to_html(blueprint)

    assert "https://example.com/assets/IMG-20240416-WA0009-e1747995653537-300x300.jpg" in html
    assert "https://images.example/pexels-photo-3873490.jpeg?auto=compress" in html
