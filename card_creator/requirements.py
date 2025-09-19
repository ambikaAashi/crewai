"""Requirement management for the card creation workflow."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Optional


URL_PATTERN = re.compile(r"https?://[^\s]+", re.IGNORECASE)

# Mapping of canonical card types to keywords that hint towards them.
# Extend this dictionary to support new categories.
CARD_TYPE_KEYWORD_MAP: dict[str, tuple[str, ...]] = {
    "personal": ("personal",),
    "business": ("business", "corporate", "company"),
    "invitation": ("invitation", "invite"),
}


def infer_card_type_from_text(text: str) -> str | None:
    """Infer card type keywords present in the given text."""

    lowered = text.lower()
    matches: list[tuple[int, str]] = []
    for card_type, keywords in CARD_TYPE_KEYWORD_MAP.items():
        for keyword in keywords:
            index = lowered.find(keyword)
            if index != -1:
                matches.append((index, card_type))
                break
    if not matches:
        return None
    matches.sort(key=lambda item: item[0])
    ordered_types: list[str] = []
    for _, card_type in matches:
        if card_type not in ordered_types:
            ordered_types.append(card_type)
    if len(ordered_types) == 1:
        return ordered_types[0]
    return " ".join(ordered_types)


@dataclass(slots=True)
class CardRequirements:
    """Structured representation of card requirements collected from the user."""

    occasion: str | None = None
    card_type: str | None = None
    size: str | None = None
    recipient: str | None = None
    relationship: str | None = None
    tone: str | None = None
    message_focus: str | None = None
    personalization_details: str | None = None
    color_palette: str | None = None
    typography: str | None = None
    visual_style: str | None = None
    must_include_elements: str | None = None
    call_to_action: str | None = None
    delivery_format: str | None = None
    deadline: str | None = None
    additional_notes: str | None = None
    brand_notes: str | None = None
    image_urls: list[str] = field(default_factory=list)

    def required_fields_missing(self) -> list[str]:
        """Return a list of required fields that are still missing."""

        missing = []
        if not self.occasion:
            missing.append("occasion")
        if not self.card_type:
            missing.append("card_type")
        if not self.size:
            missing.append("size")
        return missing

    def is_core_complete(self) -> bool:
        """Whether the three mandatory attributes are collected."""

        return not self.required_fields_missing()

    def to_summary_dict(self) -> dict[str, object]:
        """Convert to a serialisable summary dictionary."""

        return {
            "occasion": self.occasion,
            "card_type": self.card_type,
            "size": self.size,
            "recipient": self.recipient,
            "relationship": self.relationship,
            "tone": self.tone,
            "message_focus": self.message_focus,
            "personalization_details": self.personalization_details,
            "color_palette": self.color_palette,
            "typography": self.typography,
            "visual_style": self.visual_style,
            "must_include_elements": self.must_include_elements,
            "call_to_action": self.call_to_action,
            "delivery_format": self.delivery_format,
            "deadline": self.deadline,
            "additional_notes": self.additional_notes,
            "brand_notes": self.brand_notes,
            "image_urls": list(self.image_urls),
        }

    def build_pexels_query(self) -> str:
        """Construct a default query for the Pexels search."""

        keywords: list[str] = []
        if self.occasion:
            keywords.append(self.occasion)
        if self.tone:
            keywords.append(self.tone)
        if self.color_palette:
            keywords.append(self.color_palette)
        if self.visual_style:
            keywords.append(self.visual_style)
        if not keywords:
            keywords.append("beautiful card background")
        return " ".join(keywords)


@dataclass(slots=True)
class Question:
    """Represents a question that can be asked to the user."""

    id: str
    prompt_builder: Callable[[CardRequirements], str]
    field: str | None = None
    required: bool = False
    handler: Optional[Callable[[CardRequirements, str], None]] = None
    condition: Callable[[CardRequirements], bool] = lambda _: True

    def render(self, requirements: CardRequirements) -> str:
        return self.prompt_builder(requirements)

    def apply_answer(self, requirements: CardRequirements, answer: str) -> None:
        if self.handler is not None:
            self.handler(requirements, answer)
        elif self.field:
            cleaned = URL_PATTERN.sub("", answer).strip()
            setattr(requirements, self.field, cleaned or answer.strip())


class RequirementManager:
    """Stateful helper that drives the requirements interview."""

    def __init__(self) -> None:
        self.requirements = CardRequirements()
        self._question_order: list[Question] = self._build_question_bank()
        self._asked: set[str] = set()
        self._active_question: Question | None = None
        self._greeted = False

    def _build_question_bank(self) -> list[Question]:
        questions: list[Question] = [
            Question(
                id="occasion",
                field="occasion",
                required=True,
                prompt_builder=lambda _: "Aap kis occasion ke liye card banana chahte hain?",
            ),
            Question(
                id="card_type",
                field="card_type",
                required=True,
                prompt_builder=lambda _: (
                    "Kya yeh personal card hai ya business card? Agar business hai to brand/company ka"
                    " naam bhi batayein."
                ),
            ),
            Question(
                id="size",
                field="size",
                required=True,
                prompt_builder=lambda _: (
                    "Card ka size kya rakhen? (jaise 5x7 inch, A5, ya koi digital format)"
                ),
            ),
            Question(
                id="recipient",
                field="recipient",
                prompt_builder=lambda req: (
                    "Card kis ke liye hai? Agar naam ya relation bata sakein to behatar rahega."
                ),
            ),
            Question(
                id="relationship",
                field="relationship",
                prompt_builder=lambda req: (
                    "Recipient se aapka relationship kya hai? (jaise friend, client, parents)"
                ),
            ),
            Question(
                id="tone",
                field="tone",
                prompt_builder=lambda req: (
                    f"{req.occasion or 'Card'} ka tone kaise rakhna hai? (jaise elegant, fun, professional)"
                ),
            ),
            Question(
                id="message_focus",
                field="message_focus",
                prompt_builder=lambda req: (
                    "Message ka main focus kya ho? koi keyword ya feeling jo zaroor include ho?"
                ),
            ),
            Question(
                id="personalization_details",
                field="personalization_details",
                prompt_builder=lambda req: (
                    "Koi personal details ya inside jokes jo add karna chahte ho?"
                ),
            ),
            Question(
                id="color_palette",
                field="color_palette",
                prompt_builder=lambda req: (
                    "Kis color palette ya combinations ko prefer karenge?"
                ),
            ),
            Question(
                id="typography",
                field="typography",
                prompt_builder=lambda req: (
                    "Fonts kis type ke pasand karenge? (jaise handwritten, modern sans, serif)"
                ),
            ),
            Question(
                id="visual_style",
                field="visual_style",
                prompt_builder=lambda req: (
                    "Background ya illustrations ka style kya ho? (minimal, floral, abstract, etc.)"
                ),
            ),
            Question(
                id="must_include_elements",
                field="must_include_elements",
                prompt_builder=lambda req: (
                    "Koi elements ya phrases jo card par zaroor hone chahiye?"
                ),
            ),
            Question(
                id="call_to_action",
                field="call_to_action",
                prompt_builder=lambda req: (
                    "Agar business card hai to koi call-to-action ya contact info batayein?"
                ),
                condition=lambda req: (req.card_type or "").lower().startswith("business"),
            ),
            Question(
                id="brand_notes",
                field="brand_notes",
                prompt_builder=lambda req: (
                    "Brand guidelines ya logo colors share karna chahenge?"
                ),
                condition=lambda req: (req.card_type or "").lower().startswith("business"),
            ),
            Question(
                id="delivery_format",
                field="delivery_format",
                prompt_builder=lambda req: (
                    "Card ka final format kya hoga? (print-ready PDF, social media post, etc.)"
                ),
            ),
            Question(
                id="deadline",
                field="deadline",
                prompt_builder=lambda req: (
                    "Card kab tak ready chahiye? koi deadline ya event date?"
                ),
            ),
            Question(
                id="image_urls",
                handler=self._handle_image_answer,
                prompt_builder=lambda req: (
                    "Kya aapke paas koi image ya logo URLs hain jo card mein lazmi hone chahiye?"
                ),
            ),
            Question(
                id="additional_notes",
                field="additional_notes",
                prompt_builder=lambda req: (
                    "Koi aur special instruction ya note jo hume consider karna chahiye?"
                ),
            ),
        ]
        return questions

    def _handle_image_answer(self, requirements: CardRequirements, answer: str) -> None:
        urls = extract_urls(answer)
        if urls:
            for url in urls:
                if url not in requirements.image_urls:
                    requirements.image_urls.append(url)
        if urls:
            remaining = URL_PATTERN.sub("", answer).strip()
            if remaining:
                requirements.must_include_elements = merge_text(
                    requirements.must_include_elements, remaining
                )
        elif answer.strip():
            requirements.must_include_elements = merge_text(
                requirements.must_include_elements, answer.strip()
            )

    def welcome(self) -> str:
        if self._greeted:
            return ""
        self._greeted = True
        return (
            "Namaste! Main aapka card design assistant hoon. Kuch sawaalon se hum"
            " ek perfect card banayenge. Aap kisi bhi waqt 'done' likh kar design"
            " banwana start kar sakte hain jab aapko lage details complete ho gayi hain."
        )

    def next_question(self) -> str | None:
        """Return the next question text that should be asked."""

        # Prioritise mandatory fields
        for question in self._question_order:
            if question.required and getattr(self.requirements, question.field or "", None) in (None, ""):
                if question.condition(self.requirements):
                    self._active_question = question
                    self._asked.add(question.id)
                    return question.render(self.requirements)

        for question in self._question_order:
            if question.id in self._asked:
                continue
            if not question.condition(self.requirements):
                continue
            # Skip optional question if already filled via previous answer
            if question.field and getattr(self.requirements, question.field, None):
                continue
            self._active_question = question
            self._asked.add(question.id)
            return question.render(self.requirements)

        self._active_question = None
        return None

    def ingest_answer(self, answer: str) -> None:
        """Store the answer for the current active question."""

        answer = answer.strip()
        if not answer:
            return
        self._capture_urls(answer)
        if not self._active_question:
            return
        question = self._active_question
        question.apply_answer(self.requirements, answer)
        self._auto_fill_from_answer(question, answer)

    def _auto_fill_from_answer(self, question: Question, answer: str) -> None:
        if question.id == "occasion" and not (self.requirements.card_type or "").strip():
            inferred = infer_card_type_from_text(answer)
            if inferred:
                self.requirements.card_type = inferred

    def _capture_urls(self, message: str) -> None:
        urls = extract_urls(message)
        if not urls:
            return
        for url in urls:
            if url not in self.requirements.image_urls:
                self.requirements.image_urls.append(url)

    def summary(self) -> str:
        """Return a readable summary of captured requirements."""

        parts = [
            "Collected requirements:",
            f"  Occasion: {self.requirements.occasion or '—'}",
            f"  Card type: {self.requirements.card_type or '—'}",
            f"  Size: {self.requirements.size or '—'}",
        ]
        optional_fields = {
            "Recipient": self.requirements.recipient,
            "Relationship": self.requirements.relationship,
            "Tone": self.requirements.tone,
            "Message focus": self.requirements.message_focus,
            "Personal details": self.requirements.personalization_details,
            "Color palette": self.requirements.color_palette,
            "Typography": self.requirements.typography,
            "Visual style": self.requirements.visual_style,
            "Must include": self.requirements.must_include_elements,
            "Call to action": self.requirements.call_to_action,
            "Delivery format": self.requirements.delivery_format,
            "Deadline": self.requirements.deadline,
            "Additional notes": self.requirements.additional_notes,
            "Brand notes": self.requirements.brand_notes,
        }
        for label, value in optional_fields.items():
            if value:
                parts.append(f"  {label}: {value}")
        if self.requirements.image_urls:
            parts.append("  Image URLs:")
            for url in self.requirements.image_urls:
                parts.append(f"    - {url}")
        return "\n".join(parts)

    def has_more_questions(self) -> bool:
        """Whether there are more relevant questions to ask."""

        if any(
            question.required
            and getattr(self.requirements, question.field or "", None) in (None, "")
            and question.condition(self.requirements)
            for question in self._question_order
        ):
            return True
        for question in self._question_order:
            if question.id in self._asked:
                continue
            if not question.condition(self.requirements):
                continue
            if question.field and getattr(self.requirements, question.field, None):
                continue
            return True
        return False


def extract_urls(text: str) -> list[str]:
    """Extract URLs from the given text."""

    return URL_PATTERN.findall(text)


def merge_text(existing: str | None, addition: str) -> str:
    """Merge new text into an existing optional field."""

    if not existing:
        return addition
    if addition.lower() in existing.lower():
        return existing
    return f"{existing}; {addition}"


__all__ = [
    "CardRequirements",
    "RequirementManager",
    "Question",
    "extract_urls",
    "merge_text",
]
