"""Crew orchestration for creating a polished card blueprint."""
from __future__ import annotations

import json
from dataclasses import asdict
from textwrap import dedent
from typing import Any

from crewai import Agent, Crew, Process, Task
from crewai.llm import LLM

from .config import Settings
from .html_renderer import blueprint_to_html
from .pexels import PexelsPhoto, search_backgrounds
from .prompts import build_card_html_prompt
from .requirements import CardRequirements


class CardDesignCrew:
    """Coordinates specialist agents to design a card blueprint."""

    def __init__(self, settings: Settings, requirements: CardRequirements) -> None:
        self.settings = settings
        self.requirements = requirements
        self._llm = LLM(**self.settings.llm_arguments())
        self._pexels_images: list[PexelsPhoto] = []

    def gather_inspirations(self) -> list[PexelsPhoto]:
        """Collect relevant Pexels images based on the requirement set."""

        if not self._pexels_images:
            query = self.requirements.build_pexels_query()
            self._pexels_images = search_backgrounds(
                self.settings.pexels_api_key,
                query,
                per_page=6,
                orientation="landscape",
            )
        return self._pexels_images

    def run(self) -> dict[str, Any]:
        """Execute the crew and return a structured blueprint."""

        inspirations = [asdict(photo) for photo in self.gather_inspirations()]
        requirement_summary = self.requirements.to_summary_dict()
        requirement_summary["pexels_inspirations"] = inspirations

        planner = Agent(
            name="Requirement Analyst",
            role="Understand user goals and distil them into a creative brief.",
            goal="Transform user requirements into a sharp design direction for a card.",
            backstory=dedent(
                """
                Tum ek experienced design strategist ho jo card design projects ko
                structure karta hai. Tumhe ensure karna hai ki har requirement clearly
                defined ho aur koi bhi missing detail highlight ho sake.
                """
            ),
            llm=self._llm,
        )

        copywriter = Agent(
            name="Copywriter & Layout Specialist",
            role="Craft heartfelt copy and propose card layouts based on the brief.",
            goal="Deliver a final blueprint with messaging, layout and imagery guidance.",
            backstory=dedent(
                """
                Tum ek award-winning card designer ho jo typography aur layout ko bahut
                achhi tarah balance karta hai. Tumhe ensure karna hai ki final blueprint
                mein user ke diye gaye images zaroor shamil hon aur occasion ke hisaab se
                tone perfect ho.
                """
            ),
            llm=self._llm,
        )

        analysis_task = Task(
            description=dedent(
                f"""
                Neeche card project ki sari details di gayi hain:
                ```json
                {json.dumps(requirement_summary, indent=2, ensure_ascii=False)}
                ```

                Tumhara kaam hai ek concise creative brief banana jo card ke goals,
                target audience aur critical constraints ko summarise kare. Agar koi
                important information missing ho to usse list karo.

                Output ko JSON mein do with fields: "brief", "gaps".
                """
            ),
            expected_output="JSON with keys 'brief' aur 'gaps'.",
            agent=planner,
        )

        final_task = Task(
            description=dedent(
                """
                Tumhe Requirement Analyst ka brief aur sari project details mil gayi hain.
                Ab tumhara kaam hai poora card blueprint ready karna.

                Deliverables ko JSON object ki tarah present karo with keys:
                - "card_summary": short overview of the concept.
                - "messaging":
                    - "headline"
                    - "body"
                    - "closing"
                - "visual_direction":
                    - "palette"
                    - "typography"
                    - "layout"
                    - "background_image_plan"
                - "image_assets": "must_use" (sab user provided URLs) aur "pexels_options" (top 3 inspirations).
                - "production_notes": kisi bhi printing ya export ke instructions.
                - "next_questions": agar koi detail abhi bhi missing hai to unhe list karo.

                Har hal mein user dwara diye gaye saare image URLs "must_use" mein hon.
                Background_image_plan mein bataye kaunse visuals kis tarah se use honge.
                """
            ),
            expected_output="Structured JSON blueprint jisme sab sections bharay hon.",
            agent=copywriter,
        )

        crew = Crew(
            agents=[planner, copywriter],
            tasks=[analysis_task, final_task],
            process=Process.sequential,
            verbose=False,
        )

        crew_output = crew.kickoff()
        raw_payload = getattr(crew_output, "raw", crew_output)
        raw_output = self._ensure_textual_payload(raw_payload)
        blueprint = self._safe_parse_json(raw_output)

        html_preview = (
            blueprint_to_html(blueprint)
            if isinstance(blueprint, dict)
            else None
        )
        html_prompt = (
            build_card_html_prompt(blueprint)
            if isinstance(blueprint, dict)
            else None
        )
        generated_html = None
        generated_html_raw = None
        if html_prompt:
            generated_html, generated_html_raw = self._generate_final_html(html_prompt)


        return {
            "raw_output": raw_output,
            "blueprint": blueprint,
            "pexels_images": inspirations,
            "html_preview": html_preview,
            "html_generation_prompt": html_prompt,
            "generated_html": generated_html,
            "generated_html_raw": generated_html_raw,
        }

    def _ensure_textual_payload(self, payload: Any) -> str:
        if payload is None:
            return ""
        if isinstance(payload, str):
            return payload
        if isinstance(payload, (bytes, bytearray)):
            return payload.decode("utf-8", errors="replace")
        if isinstance(payload, (dict, list)):
            try:
                return json.dumps(payload)
            except (TypeError, ValueError):
                return str(payload)
        return str(payload)

    def _safe_parse_json(self, payload: str) -> dict[str, Any] | None:
        """Best-effort JSON parser that tolerates surrounding chatter."""

        if not payload:
            return None

        payload = payload.strip()
        if not payload:
            return None

        for candidate in self._iter_json_candidates(payload):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    def _iter_json_candidates(self, payload: str) -> list[str]:
        """Collect potential JSON snippets contained within the payload."""

        candidates: list[str] = []

        def collect_segment(start_char: str, end_char: str) -> None:
            start = payload.find(start_char)
            while start != -1:
                segment = self._extract_balanced_segment(payload, start, start_char, end_char)
                if segment:
                    candidates.append(segment)
                    return
                start = payload.find(start_char, start + 1)

        collect_segment("{", "}")
        collect_segment("[", "]")

        if not candidates:
            candidates.append(payload)

        return candidates

    def _generate_final_html(self, prompt: str) -> tuple[str | None, str | None]:
        """Call the configured LLM to turn the prompt into production HTML."""

        if not prompt:
            return None, None

        try:
            response = self._llm.call(prompt)
        except Exception:  # pragma: no cover - LLM errors handled gracefully
            return None, None

        raw_output = self._ensure_textual_payload(response)
        if not raw_output.strip():
            return None, raw_output

        html = self._extract_html_document(raw_output)
        return html, raw_output

    def _extract_html_document(self, payload: str) -> str | None:
        """Best-effort extractor for a complete HTML document in ``payload``."""

        if not payload:
            return None

        text = payload.strip()
        if not text:
            return None

        if text.startswith("```"):
            text = self._strip_code_fences(text)
            if not text:
                return None

        lower = text.lower()
        doc_start = lower.find("<!doctype")
        html_start = lower.find("<html")

        start_index: int | None = None
        if doc_start != -1 and html_start != -1:
            start_index = min(doc_start, html_start)
        elif doc_start != -1:
            start_index = doc_start
        elif html_start != -1:
            start_index = html_start

        if start_index is None:
            return None

        end_index = lower.rfind("</html>")
        if end_index != -1:
            end_index += len("</html>")
            return text[start_index:end_index].strip()

        if start_index == 0:
            return text

        return text[start_index:].strip() if "</html" in lower[start_index:] else None

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        lines = text.splitlines()
        if not lines:
            return ""

        if lines[0].strip().startswith("```"):
            lines = lines[1:]

        while lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]

        return "\n".join(lines).strip()
            return None

        payload = payload.strip()
        if not payload:
            return None

        for candidate in self._iter_json_candidates(payload):
            try:
                parsed = json.loads(candidate)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed
        return None

    def _iter_json_candidates(self, payload: str) -> list[str]:
        """Collect potential JSON snippets contained within the payload."""

        candidates: list[str] = []

        def collect_segment(start_char: str, end_char: str) -> None:
            start = payload.find(start_char)
            while start != -1:
                segment = self._extract_balanced_segment(payload, start, start_char, end_char)
                if segment:
                    candidates.append(segment)
                    return
                start = payload.find(start_char, start + 1)

        collect_segment("{", "}")
        collect_segment("[", "]")

        if not candidates:
            candidates.append(payload)

        return candidates

    @staticmethod
    def _extract_balanced_segment(message: str, start: int, opener: str, closer: str) -> str | None:
        """Return the smallest substring with balanced braces starting at ``start``."""

        depth = 0
        in_string = False
        escape = False
        for index in range(start, len(message)):
            char = message[index]
            if in_string:
                if escape:
                    escape = False
                elif char == "\\":
                    escape = True
                elif char == '"':
                    in_string = False
                continue

            if char == '"':
                in_string = True
                continue

            if char == opener:
                depth += 1
            elif char == closer:
                depth -= 1
                if depth == 0:
                    return message[start : index + 1]

        return None


__all__ = ["CardDesignCrew"]
