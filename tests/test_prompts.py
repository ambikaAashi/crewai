from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from card_creator.prompts import build_card_html_prompt


def test_build_card_html_prompt_includes_core_sections() -> None:
    blueprint = {
        "card_summary": "Elegant engagement announcement",
        "messaging": {
            "headline": "She said yes!",
            "body": "Join us as we toast to a lifetime of love.",
            "closing": "With love, Priya & Arjun",
        },
        "visual_direction": {
            "palette": ["#D4AF37", "#F8EDEB"],
            "typography": "Modern serif for headings with clean sans body",
            "layout": "Split layout with photo on the left and copy on the right",
            "background_image_plan": "Subtle glitter gradient with soft vignette",
        },
        "image_assets": {
            "must_use": ["https://example.com/uploads/couple.jpg"],
            "pexels_options": [
                {
                    "image_url": " https://images.pexels.com/photos/12345/pexels-photo.jpeg?auto=c\nompress ",
                }
            ],
        },
        "production_notes": ["Use foil-friendly colour choices"],
        "next_questions": ["Confirm final RSVP date"],
    }

    prompt = build_card_html_prompt(blueprint)

    assert "Elegant engagement announcement" in prompt
    assert "Headline: She said yes!" in prompt
    assert "-   - #D4AF37" in prompt or "#D4AF37" in prompt
    assert "https://example.com/uploads/couple.jpg" in prompt
    assert "https://images.pexels.com/photos/12345/pexels-photo.jpeg?auto=compress" in prompt
    assert "Use foil-friendly colour choices" in prompt
    assert "Confirm final RSVP date" in prompt
    assert "Do not include any JavaScript." in prompt


def test_build_card_html_prompt_handles_minimal_blueprint() -> None:
    prompt = build_card_html_prompt({})
    assert "Do not include any JavaScript." in prompt
    assert "Accessibility and formatting requirements" in prompt
