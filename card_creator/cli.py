"""Command line interface for the card creation crew."""
from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

from .config import Settings
from .crew import CardDesignCrew
from .requirements import RequirementManager

app = typer.Typer(help="Interactive assistant for designing bespoke cards.")


@app.command()
def chat() -> None:
    """Start an interactive chat to collect requirements and design a card."""

    console = Console()
    manager = RequirementManager()
    welcome = manager.welcome()
    if welcome:
        console.print(f"[bold green]{welcome}[/bold green]")

    question = manager.next_question()
    while question:
        console.print(f"\n[bold cyan]{question}[/bold cyan]")
        answer = Prompt.ask("Aapka jawab")
        normalized = answer.strip().lower()
        if normalized in {"done", "design banao", "design shuru karo", "generate"}:
            if manager.requirements.is_core_complete():
                console.print("Theek hai! Main ab tak ki details ke basis par design banaata hoon.")
                break
            missing = ", ".join(manager.requirements.required_fields_missing())
            console.print(
                f"[red]Abhi yeh important cheezein missing hain: {missing}. Pehle inhe share karein.[/red]"
            )
            continue
        manager.ingest_answer(answer)
        question = manager.next_question()

    if not manager.requirements.is_core_complete():
        console.print(
            "[bold red]Card design shuru karne se pehle occasion, card type aur size zaroori hain.[/bold red]"
        )
        return

    console.print("\n[bold]Yeh hai ab tak ka summary:[/bold]")
    console.print(manager.summary())

    if not typer.confirm("Kya aap chahte hain ki main card blueprint generate karu?", default=True):
        console.print("Thik hai! Aap kabhi bhi dubara run kar sakte hain.")
        return

    settings = Settings()
    try:
        crew = CardDesignCrew(settings, manager.requirements)
        result = crew.run()
    except ValueError as exc:
        console.print(f"[bold red]Configuration error:[/bold red] {exc}")
        console.print(
            "Kripya environment variables set karein: OPENAI_API_KEY ya SAMBANOVA_API_KEY aur PEXELS_API_KEY."
        )
        raise typer.Exit(code=1) from exc
    except Exception as exc:  # pragma: no cover - defensive guard for runtime issues
        console.print(f"[bold red]Crew execution failed:[/bold red] {exc}")
        raise typer.Exit(code=1) from exc

    blueprint = result.get("blueprint")
    if blueprint:
        console.print("\n[bold green]Card Blueprint Ready![/bold green]")
        console.print(json.dumps(blueprint, indent=2, ensure_ascii=False))
    else:
        console.print("\n[bold yellow]LLM se JSON parse nahi ho paya. Raw response neeche diya gaya hai:[/bold yellow]")
        console.print(result.get("raw_output"))

    html_preview = result.get("html_preview")
    if html_preview:
        console.print("\n[bold]HTML Preview:[/bold]")
        console.print(html_preview)
        console.print(
            "\nIs HTML ko copy karke kisi .html file mein save karein aur browser mein khol kar card dekh sakte hain."
        )

    html_prompt = result.get("html_generation_prompt")
    if html_prompt:
        console.print("\n[bold]OpenAI/LLM HTML prompt:[/bold]")
        console.print(html_prompt)
        console.print(
            "\nIs prompt ko ChatGPT ya kisi bhi code-generation model mein paste karke bespoke card HTML banwa sakte hain."
        )

    generated_html = result.get("generated_html")
    if generated_html:
        console.print("\n[bold]LLM se generated final HTML:[/bold]")
        console.print(generated_html)
        console.print(
            "\nIs final HTML ko .html file mein save karke directly browser mein khol sakte hain."
        )
    else:
        generated_html_raw = result.get("generated_html_raw")
        if generated_html_raw:
            console.print(
                "\n[bold yellow]LLM se HTML response aaya par clean extract nahi ho paya. Raw response neeche diya gaya hai:[/bold yellow]"
            )
            console.print(generated_html_raw)

    inspirations = result.get("pexels_images", [])
    if inspirations:
        console.print("\n[bold]Inspiring backgrounds from Pexels:[/bold]")
        table = Table("Preview", "Photographer", "Avg. Color")
        for photo in inspirations:
            table.add_row(photo.get("image_url", ""), photo.get("photographer", ""), photo.get("avg_color", ""))
        console.print(table)


def run() -> None:
    """Entry point used by ``python -m card_creator.cli``."""

    app()


if __name__ == "__main__":  # pragma: no cover
    run()
