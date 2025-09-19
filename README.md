# CrewAI Card Creator

Yeh project CrewAI ka use karke ek interactive agentic system banata hai jo kisi bhi occasion ke liye beautiful card design blueprint ready karta hai. System Hindi + English tone mein user se smart questions karta hai, jab tak sari zaroori details collect na ho jayein. Core information jo hamisha collect hoti hai:

1. Occasion kis ke liye hai
2. Card personal hai ya business
3. Card ka size kya hai

Iske baad assistant additional context jaise tone, colors, imagery, deadlines wagairah poochta hai. Agar user koi image URL share karta hai to woh final blueprint mein **must-use** assets ke taur par lock ho jata hai. Background inspiration ke liye Pexels API ka istemal kiya ja sakta hai.

## Features

- Rule-based requirement interview jo ensure karta hai ki core fields kabhi skip na hon.
- Automatic URL detection jisse user provided images secure rahte hain.
- CrewAI based multi-agent workflow jo creative brief aur final card blueprint (JSON format) generate karta hai.
- Pexels API integration se background inspiration fetch karta hai.
- Rich + Typer CLI experience for an interactive chatbot style flow.

## Installation

```bash
pip install -e .
```

Ya phir virtual environment setup karke `pip install -e .[dev]` run karein agar tests bhi execute karne hain.

## Environment variables

System ko run karne se pehle neeche wali keys configure karein (real values use karein):

```bash
export OPENAI_API_KEY="..."
# ya agar SambaNova prefer karna ho to
# export CARD_CREW_PROVIDER="sambanova"
# export SAMBANOVA_API_KEY="..."

export PEXELS_API_KEY="..."
```

Aap `CARD_CREW_MODEL`, `CARD_CREW_TEMPERATURE` wagairah optional overrides bhi set kar sakte hain.

## Usage

Interactive chat start karne ke liye:

```bash
card-crew chat
```

Ya phir:

```bash
python -m card_creator.cli chat
```

CLI aap se step-by-step sawaal puchega. Jab aapko lage ki sab details mil gayi hain to `done` likh kar blueprint generation trigger karein.

## Tests

```bash
pytest
```

## Notes

- Project network calls (OpenAI/SambaNova/Pexels) tabhi chalenge jab valid API keys aur internet connectivity present ho.
- Agar LLM se JSON response parse na ho paye to raw text CLI mein display ho jayega.
