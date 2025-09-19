from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parents[1]))

from card_creator.requirements import RequirementManager, extract_urls, merge_text


def test_requirement_manager_collects_core_fields():
    manager = RequirementManager()
    q1 = manager.next_question()
    assert "occasion" in q1.lower()
    manager.ingest_answer("Birthday party")

    q2 = manager.next_question()
    assert "personal" in q2.lower() or "business" in q2.lower()
    manager.ingest_answer("Personal card")

    q3 = manager.next_question()
    assert "size" in q3.lower()
    manager.ingest_answer("5x7 inch")

    assert manager.requirements.is_core_complete()
    assert not manager.requirements.required_fields_missing()


def test_urls_are_extracted_and_stored():
    manager = RequirementManager()
    manager.next_question()
    manager.ingest_answer("Birthday with image https://example.com/pic.png")
    assert "https://example.com/pic.png" in manager.requirements.image_urls
    assert manager.requirements.occasion == "Birthday with image"


def test_merge_text_adds_unique_segments():
    assert merge_text(None, "A") == "A"
    assert merge_text("A", "B") == "A; B"
    assert merge_text("Include logo", "logo") == "Include logo"


def test_extract_urls_handles_multiple_entries():
    text = "Use https://one.example/img.jpg and also http://two.example/a.png"
    urls = extract_urls(text)
    assert urls == [
        "https://one.example/img.jpg",
        "http://two.example/a.png",
    ]
