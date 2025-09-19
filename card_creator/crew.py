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

        return {
            "raw_output": raw_output,
            "blueprint": blueprint,
            "pexels_images": inspirations,
            "html_preview": html_preview,
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
        try:
            return json.loads(payload)
        except (TypeError, json.JSONDecodeError):
            return None


__all__ = ["CardDesignCrew"]
