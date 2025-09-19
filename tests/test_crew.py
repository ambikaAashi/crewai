from pathlib import Path
import sys
from textwrap import dedent

sys.path.append(str(Path(__file__).resolve().parents[1]))

from card_creator.crew import CardDesignCrew


def _make_crew() -> CardDesignCrew:
    crew = object.__new__(CardDesignCrew)
    return crew  # type: ignore[return-value]


def test_safe_parse_json_with_trailing_notes() -> None:
    payload = dedent(
        """
        {
          "card_summary": "A heartfelt invitation for Ambika's birthday party, designed to evoke emotions and encourage attendance from Narotam, a valued colleague.",
          "messaging": {
            "headline": "Join Us for a Special Celebration!",
            "body": "Dear Narotam, we would be thrilled to have you at Ambika's birthday party! It's a day to celebrate joy, laughter, and wonderful memories. Your presence would mean the world to us.",
            "closing": "Looking forward to celebrating together!"
          },
          "visual_direction": {
            "palette": "Rich red tones to evoke warmth and excitement, complemented by soft floral accents.",
            "typography": "Handwritten style for a personal touch, ensuring the text feels inviting and friendly.",
            "layout": "Centered layout with the headline at the top, followed by the body text and closing at the bottom. Floral elements will frame the card edges.",
            "background_image_plan": "The background will feature a soft-focus floral image to create a warm and inviting atmosphere, with the text overlaying in a contrasting color for readability."
          },
          "image_assets": {
            "must_use": [
              "https://reflect.webgarh.com/wp-content/uploads/2025/05/IMG-20240416-WA0009-e1747995653537-300x300.jpg"
            ],
            "pexels_options": [
              "https://images.pexels.com/photos/20849554/pexels-photo-20849554.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940"
            ]
          },
          "production_notes": "Ensure high-quality printing with a matte finish to enhance the handwritten typography. Export in a format suitable for social media sharing.",
          "next_questions": [
            "What is the date and time of the birthday party?",
            "What are the RSVP details?"
          ]
        }

        Inspiring backgrounds from Pexels:
        - https://images.pexels.com/photos/3873490/pexels-photo-3873490.jpeg
        """
    ).strip()

    crew = _make_crew()
    parsed = CardDesignCrew._safe_parse_json(crew, payload)

    assert parsed is not None
    assert parsed["card_summary"].startswith("A heartfelt invitation")


def test_safe_parse_json_ignores_preceding_text() -> None:
    payload = dedent(
        """
        Here is the requested blueprint:
        ```json
        {"card_summary": "Simple card", "messaging": {"headline": "Hi", "body": "Hello", "closing": "Bye"}}
        ```
        Let me know if you need anything else.
        """
    )

    crew = _make_crew()
    parsed = CardDesignCrew._safe_parse_json(crew, payload)

    assert parsed is not None
    assert parsed["messaging"]["headline"] == "Hi"


def test_safe_parse_json_returns_none_when_absent() -> None:
    crew = _make_crew()
    assert CardDesignCrew._safe_parse_json(crew, "No JSON here") is None
