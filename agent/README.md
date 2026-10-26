# Road Safety Policy Advisor

A compact policy decision-support CLI for the article's question: why do deaths rise despite stricter rules, and which enforcement-focused policies could help? It uses three distinct analysis lenses, saves each completed stage to a scenario-specific filesystem sandbox, calculates transparent deterministic scores, surfaces conflicts, and writes a conditional decision report.

## Run

Requires Python 3.10+ and a Groq API key. The core uses only the standard library and Groq's OpenAI-compatible HTTP endpoint.

1. Copy `.env.example` to `.env` and set `GROQ_API_KEY` (or export it in your shell).
2. Optionally set `GROQ_MODEL`.
3. From the repository root run:

   ```bash
   python agent/main.py "A city has many traffic violations, unpaid e-challans, and repeat offenders. Which intervention should be prioritized?"
   ```

The final Markdown report appears under `agent/output/`; intermediate state, findings, and decisions are under `agent/sandbox/runs/<scenario-id>/`.

## Resume behavior

The normalized scenario text is SHA-256 hashed into a run ID. Each stage writes an atomic JSON artifact and then records that stage in `state/run_state.json`. On the same scenario, completed stages with readable artifacts are reused and the first incomplete stage runs next. A different scenario gets a different run directory. If an API key is replaced after a 429 or other interruption, rerun the same command; the key is read from the current environment and is never written to state or logs.

## Workflow

1. Enforcement and compliance research lens.
2. Driver behaviour and attitude research lens.
3. Technology and implementation research lens.
4. Policy options with provisional qualitative ratings.
5. Deterministic score calculation: `2 × impact + feasibility − cost − risk`.
6. Separate conflict/agreement analysis.
7. Conditional recommendation and Markdown decision report.

The arithmetic is deterministic; its inputs are model judgements, not measured outcomes. Inspect the raw ratings, evidence basis, conflicts and conditions. The HTTP client retries transient failures at most twice and stops immediately on rate limiting. No retry loop consumes requests indefinitely.

## Research limitation

This prototype does not have a live web-search tool. Groq generates lens-based analysis from the scenario and its model knowledge, and is explicitly told not to claim browsing or invent citations. Findings may still be incomplete or wrong: verify primary-source URLs and local policy/legal requirements before using recommendations. The supplied assignment brief is context, not independent validation. For a stronger exam demo, provide curated source excerpts or integrate a verified search tool.

## State and safety

- `.env` is ignored; the key is never placed in a request artifact, prompt, report or log.
- Scenario-specific folders prevent cross-scenario reuse.
- JSON artifacts use write-to-temp plus atomic replace.
- Only a successful stage is marked complete; failed/malformed calls leave it pending.
- `last_error` is an API error message with no credential, but review provider error text before sharing logs.

## Example state layout

```text
sandbox/runs/<scenario-id>/
├── state/run_state.json
├── findings/{enforcement_compliance,driver_behaviour,technology_implementation}.json
└── decisions/{policy_options,scored_options,conflicts,report}.json
```

## Deliberate scope limits

No local QLoRA pipeline, database, PPT generation, or deepagents dependency is included. The straightforward staged orchestrator demonstrates orchestration and resumability with a small, inspectable interface. Optional LangSmith tracing can be added if needed; it is not required for the core run.

## Reading the source

Agent functions include purpose, input, output, and action notes. Start at `main.py` to see how settings and saved state are loaded, then follow `run_workflow()` in `orchestration.py` to understand the stages.
