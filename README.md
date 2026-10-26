# Road Safety: Beyond the Licence

A compact, spec-driven exam project with two parts: an evidence-led road-safety explainer and a resumable policy recommendation agent. The local project intentionally contains no QLoRA training folder; that work belongs in Google Colab.

## Project areas

- [`website/`](website/README.md) — responsive, JSON-driven explainer with interactive driving scenarios.
- [`agent/`](agent/README.md) — Groq-backed, staged policy workflow with persistent state, deterministic scoring, and resume support.

## Run

Open `website/index.html` in a browser, or serve it from the repository root with `python -m http.server 8000` and visit `/website/`.

For the agent, use Python 3.10+; copy `agent/.env.example` to `agent/.env`, add `GROQ_API_KEY` (and optionally a model name), then run `python agent/main.py "A city has many unpaid e-challans and repeat offenders."`. State and reports are stored under `agent/sandbox/` and `agent/output/`.

The supplied assignment brief is the source for article figures. Other claims are marked for verification and should be sourced before policy use. See each project README for limits and workflow.
