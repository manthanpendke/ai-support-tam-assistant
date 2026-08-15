# AI Support & TAM Assistant

Production-minded AI system for:
1. Intelligent ticket triage
2. TAM account health summarisation
3. Evaluation and regression testing
4. Production design considerations

## Current milestone

Milestone 1 contains the supplied mock datasets and a validated data-access layer.

## Data

- `data/tickets.json` — supplied mock support tickets
- `data/accounts.json` — supplied mock customer accounts

Use only the supplied mock data and knowledge base for the assignment.

## Setup

```bash
python -m venv .venv
```

Activate the environment, then:

```bash
pip install -r requirements.txt
pytest -q
python run.py
```

## Planned architecture

```text
FastAPI / Streamlit
        |
   Agent services
     /       Triage       Account Health
   |              |
   +---- RAG -----+
        |
  Knowledge Base
```

More components will be added milestone by milestone.
