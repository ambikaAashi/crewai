"""Configuration helpers for the card creator crew."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class Settings:
    """Runtime configuration for the card creation system."""

    openai_api_key: str | None = field(default_factory=lambda: os.getenv("OPENAI_API_KEY"))
    sambanova_api_key: str | None = field(default_factory=lambda: os.getenv("SAMBANOVA_API_KEY"))
    pexels_api_key: str | None = field(default_factory=lambda: os.getenv("PEXELS_API_KEY"))
    model: str = field(default_factory=lambda: os.getenv("CARD_CREW_MODEL", "gpt-4o-mini"))
    provider: str = field(default_factory=lambda: os.getenv("CARD_CREW_PROVIDER", "openai"))
    organization: str | None = field(default_factory=lambda: os.getenv("OPENAI_ORG"))
    temperature: float = field(default_factory=lambda: float(os.getenv("CARD_CREW_TEMPERATURE", "0.4")))

    def ensure_llm_credentials(self) -> None:
        """Validate that we have credentials for the selected provider."""

        if self.provider == "openai" and not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY is required when provider is set to 'openai'."
            )
        if self.provider == "sambanova" and not self.sambanova_api_key:
            raise ValueError(
                "SAMBANOVA_API_KEY is required when provider is set to 'sambanova'."
            )

    def llm_arguments(self) -> dict[str, object]:
        """Return keyword arguments to construct a :class:`crewai.llm.LLM`."""

        self.ensure_llm_credentials()
        kwargs: dict[str, object] = {
            "model": self.model,
            "temperature": self.temperature,
        }
        if self.provider == "openai":
            kwargs["api_key"] = self.openai_api_key
            if self.organization:
                kwargs["organization"] = self.organization
        elif self.provider == "sambanova":
            kwargs["api_key"] = self.sambanova_api_key
            kwargs["base_url"] = os.getenv(
                "SAMBANOVA_BASE_URL", "https://api.sambanova.ai/v1"
            )
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
        return kwargs


__all__ = ["Settings"]
