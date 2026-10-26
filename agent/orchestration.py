"""Resumable research -> policy analysis -> trade-off -> recommendation workflow."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from model import GroqClient
from state import OUTPUT, atomic_json, read_json, save_state

LENSES = {
    "enforcement_compliance": "Enforcement and compliance: examine detection, e-challan collection, due process, repeat-offender escalation, and what evidence would support each option.",
    "driver_behaviour": "Driver behaviour and attitude: examine why knowledge and licence testing may not transfer to safe decisions, and how targeted education or behavioural interventions could complement enforcement.",
    "technology_implementation": "Technology and implementation: examine automated enforcement and digital systems, including feasibility, cost, privacy, fairness, data quality, and implementation risks.",
}
RESEARCH_SYSTEM = """You are a cautious policy research analyst. Return concise Markdown with: key findings; evidence and source URLs (only URLs you can identify confidently); uncertainty/limitations; policy implications. Never invent citations, statistics, laws, or causal claims. Distinguish user-provided context from externally verified evidence. If you cannot substantiate a claim, label it as a hypothesis or research question. Do not claim to have browsed."""


def _json_response(text: str) -> dict:
    """Purpose: Convert a model response into a Python dictionary.

    Input: Text that should contain a JSON object, optionally in a code fence.
    Output: The decoded dictionary.
    What it does: Removes a simple Markdown fence and rejects non-object JSON.
    """
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("Expected a JSON object")
    return value


def _stage(run_dir: Path, state: dict, name: str, output_path: Path, action) -> Any:
    """Purpose: Reuse a completed stage or run and save it once.

    Input: The run folder/state, stage name, output path, and a no-argument action.
    Output: The saved or newly created stage result.
    What it does: Validates old artifacts, recovers a missing completion marker,
    or executes the action and atomically saves its result before continuing.
    """
    completed = set(state.get("completed_stages", []))
    existing = read_json(output_path)
    valid = isinstance(existing, dict) and bool(existing)
    if name.startswith("research:"):
        valid = valid and isinstance(existing.get("finding"), str) and bool(existing["finding"].strip())
    elif name == "policy_analysis":
        valid = valid and isinstance(existing.get("policies"), list) and bool(existing["policies"])
    elif name == "deterministic_scoring":
        valid = valid and isinstance(existing.get("policies"), list)
    elif name == "conflict_analysis":
        valid = valid and isinstance(existing.get("conflicts"), list)
    elif name == "final_recommendation":
        valid = valid and isinstance(existing.get("recommendation"), str) and bool(existing["recommendation"].strip())
    if valid:
        # Recover the narrow crash window where the atomic artifact landed but the
        # completion marker did not. This avoids repeating a paid API request.
        if name not in completed:
            state["completed_stages"] = sorted(completed | {name})
            save_state(run_dir, state)
        print(f"  ✓ {name} already complete; reusing saved artifact")
        return existing
    print(f"  → {name}")
    result = action()
    atomic_json(output_path, result)
    state["completed_stages"] = sorted(completed | {name})
    state["status"] = "in_progress"
    save_state(run_dir, state)
    return result


def run_workflow(client: GroqClient, run_dir: Path, state: dict) -> Path:
    """Purpose: Coordinate the complete research-to-recommendation workflow.

    Input: Groq client, scenario-specific run folder, and persisted run state.
    Output: Path to the final Markdown decision report.
    What it does: Runs three research lenses, analyzes policy options, scores
    them, identifies conflicts, and writes a conditional recommendation.
    """
    scenario = state["scenario"]
    findings_dir = run_dir / "findings"
    findings: dict[str, dict] = {}
    print(f"Scenario: {scenario}\nRun: {state['run_id']}\n")
    for lens, description in LENSES.items():
        path = findings_dir / f"{lens}.json"
        findings[lens] = _stage(
            run_dir,
            state,
            f"research:{lens}",
            path,
            lambda description=description: research_one_lens(
                client, scenario, description
            ),
        )

    policy_path = run_dir / "decisions" / "policy_options.json"
    policy_data = _stage(
        run_dir,
        state,
        "policy_analysis",
        policy_path,
        lambda: generate_policy_options(client, scenario, findings),
    )

    # Deterministic arithmetic over explicitly provisional model ratings; all raw ratings remain visible.
    score_path = run_dir / "decisions" / "scored_options.json"
    scored = _stage(
        run_dir,
        state,
        "deterministic_scoring",
        score_path,
        lambda: score_policy_options(policy_data),
    )

    conflict_path = run_dir / "decisions" / "conflicts.json"
    conflict_data = _stage(
        run_dir,
        state,
        "conflict_analysis",
        conflict_path,
        lambda: analyze_conflicts(client, scenario, findings),
    )

    report_path = OUTPUT / f"{state['run_id']}-decision_report.md"
    report_data = _stage(
        run_dir,
        state,
        "final_recommendation",
        run_dir / "decisions" / "report.json",
        lambda: generate_recommendation(
            client, scenario, scored, conflict_data, findings
        ),
    )

    report = _render_report(state, findings, scored, conflict_data, report_data)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    state["status"] = "complete"
    state["report_path"] = str(report_path.relative_to(OUTPUT.parent))
    state["completed_stages"] = sorted(set(state.get("completed_stages", [])) | {"report_written"})
    save_state(run_dir, state)
    return report_path


def research_one_lens(client: GroqClient, scenario: str, description: str) -> dict:
    """Purpose: Ask one specialist lens to analyze the policy scenario.

    Input: Groq client, scenario text, and a single lens description.
    Output: A dictionary with the lens name and its saved text finding.
    What it does: Adds article context while instructing the model to show gaps
    and avoid pretending that model knowledge is live web research.
    """
    article_context = (
        "The supplied assignment brief says Indian road deaths rose from about "
        "1.56 lakh (2015) to 1.84 lakh (2025), Vietnam's reported rate is about "
        "14 per lakh with a 95% test pass mark, Singapore's rate about 1.8 per "
        "lakh, the proposed Indian pass threshold is 75%, and about ₹24,000 "
        "crore in unpaid e-challans is cited. Treat these solely as user-provided "
        "article context, not verified external evidence. Analyze options and "
        "identify what evidence is missing."
    )
    user_prompt = (
        f"Problem to investigate: {scenario}\n\n"
        f"Research lens: {description}\n\n{article_context}"
    )

    return {
        "lens": description,
        "finding": client.complete(RESEARCH_SYSTEM, user_prompt),
    }


def generate_policy_options(
    client: GroqClient, scenario: str, findings: dict
) -> dict:
    """Purpose: Ask the model to create a small set of policy choices.

    Input: Groq client, scenario text, and the three saved lens findings.
    Output: A dictionary containing a policies list.
    What it does: Requests distinct options with trade-offs and provisional
    ratings, while labeling unsupported claims as assumptions.
    """
    system_prompt = (
        "You are a policy decision analyst. Return valid JSON only. Do not "
        "fabricate facts or present model judgements as measured effects. "
        "Candidate policies should be relevant to the scenario. For each policy "
        "include id, name, rationale, expected_impact, feasibility, cost, and "
        "risk as integer ratings 1-5, where 5 is high (cost and risk 5 are "
        "unfavorable). Also include benefits, risks, trade_offs, conditions, "
        "and evidence_basis strings. Ratings are qualitative provisional "
        "hypotheses, not observed measurements."
    )
    user_prompt = (
        f"Problem: {scenario}\n\n"
        f"Research lens findings:\n{json.dumps(findings, ensure_ascii=False)}\n\n"
        "Return {\"policies\":[...]} with 3-5 distinct policy options, "
        "including enforcement-focused measures where relevant and at least "
        "one complementary behaviour measure. Include a clear evidence_basis, "
        "and mark unsupported parts as assumptions."
    )
    response = client.complete(system_prompt, user_prompt, json_mode=True)
    return _json_response(response)


def score_policy_options(policy_data: dict) -> dict:
    """Purpose: Calculate the transparent score for every policy option.

    Input: A dictionary whose policies contain 1–5 qualitative ratings.
    Output: A dictionary with the formula and scored policy list.
    What it does: Uses Python arithmetic so the same ratings always produce
    the same score; it does not claim that the ratings are empirical evidence.
    """
    policies = []

    for policy in policy_data.get("policies", []):
        impact = _rating(policy, "expected_impact")
        feasibility = _rating(policy, "feasibility")
        cost = _rating(policy, "cost")
        risk = _rating(policy, "risk")
        score = (2 * impact) + feasibility - cost - risk
        policies.append({**policy, "score": score})

    return {
        "method": (
            "score = 2*impact + feasibility - cost - risk; higher is preferred. "
            "Ratings are qualitative model judgements, not empirical evidence."
        ),
        "policies": policies,
    }


def analyze_conflicts(client: GroqClient, scenario: str, findings: dict) -> dict:
    """Purpose: Ask the model to preserve disagreements between research lenses.

    Input: Groq client, scenario text, and findings from the lenses.
    Output: A dictionary with conflicts, agreements and an explanatory note.
    What it does: Requests both sides of a disagreement and its policy implication.
    """
    system_prompt = (
        "Identify material disagreements or tensions across research lenses. "
        "Do not flatten conflicts. Return valid JSON "
        "{\"conflicts\":[{\"lens_a\":\"...\",\"finding_a\":\"...\","
        "\"lens_b\":\"...\",\"finding_b\":\"...\","
        "\"implication\":\"...\"}],\"agreements\":[...],\"note\":\"...\"}. "
        "If no substantiated disagreement appears, say so and identify unresolved "
        "tensions as such. Do not invent facts."
    )
    user_prompt = (
        f"Problem: {scenario}\nFindings:\n"
        f"{json.dumps(findings, ensure_ascii=False)}"
    )
    response = client.complete(system_prompt, user_prompt, json_mode=True)
    return _json_response(response)


def generate_recommendation(
    client: GroqClient,
    scenario: str,
    scored: dict,
    conflicts: dict,
    findings: dict,
) -> dict:
    """Purpose: Generate the final conditional policy recommendation.

    Input: Groq client, scenario, scored options, conflicts, and research.
    Output: A dictionary with recommendation, reasons, conditions and limitations.
    What it does: Uses the prior stages and asks what evidence could change the
    choice instead of presenting an unconditional answer.
    """
    system_prompt = (
        "You are the final policy advisor. Return valid JSON "
        "{\"recommendation\":\"...\",\"why\":\"...\",\"conditions\":[...],"
        "\"what_would_change_this\":[...],\"limitations\":[...]} . Make a "
        "conditional recommendation, compare expected impact and trade-offs, "
        "use the computed score only as a transparent aid, explicitly mention "
        "conflicts, and never overstate evidence. Cite source URLs only when "
        "present in research findings. Say when additional local evidence is required."
    )
    user_prompt = (
        f"Scenario: {scenario}\n"
        f"Scored policy options:\n{json.dumps(scored, ensure_ascii=False)}\n"
        f"Conflicts:\n{json.dumps(conflicts, ensure_ascii=False)}\n"
        f"Research:\n{json.dumps(findings, ensure_ascii=False)}"
    )
    response = client.complete(system_prompt, user_prompt, json_mode=True)
    return _json_response(response)


def _rating(policy: dict, key: str) -> int:
    """Purpose: Read one policy rating safely as an integer from 1 to 5.

    Input: A policy dictionary and the rating field name.
    Output: A valid rating, using 3 when the supplied value is missing/invalid.
    What it does: Keeps the scoring formula safe from malformed model output.
    """
    try:
        return max(1, min(5, int(policy.get(key, 3))))
    except (TypeError, ValueError):
        return 3


def _render_report(state: dict, findings: dict, scored: dict, conflicts: dict, recommendation: dict) -> str:
    """Purpose: Turn saved analysis into a readable Markdown report.

    Input: State, research findings, scores, conflicts, and recommendation data.
    Output: The complete report as a string.
    What it does: Presents evidence, trade-offs, conflicts and caveats in order.
    """
    lines = [
        "# Road Safety Policy Decision Report",
        "",
        f"**Scenario:** {state['scenario']}",
        f"**Run ID:** `{state['run_id']}`",
        "",
        "> Research is model-assisted and not live web research. Treat unsupported claims and qualitative ratings as hypotheses; verify cited sources before policy use.",
        "",
        "## Research lenses",
    ]

    # Add each specialist's finding under a clearly named heading.
    for key, value in findings.items():
        lines += [f"### {key.replace('_', ' ').title()}", value.get("finding", "")]

    # Show the formula and the raw ratings alongside the calculated score.
    lines += [
        "## Policy comparison",
        "",
        scored.get("method", ""),
        "",
        "| Policy | Impact | Feasibility | Cost | Risk | Score |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for policy in scored.get("policies", []):
        lines.append(
            f"| {policy.get('name', 'Option')} "
            f"| {policy.get('expected_impact', 3)} "
            f"| {policy.get('feasibility', 3)} "
            f"| {policy.get('cost', 3)} "
            f"| {policy.get('risk', 3)} "
            f"| {policy.get('score', 0)} |"
        )

    # Give every option the qualitative explanation behind its ratings.
    for policy in scored.get("policies", []):
        lines += [
            f"### {policy.get('name', 'Policy')}",
            f"**Rationale:** {policy.get('rationale', '')}",
            f"**Benefits:** {policy.get('benefits', '')}",
            f"**Risks:** {policy.get('risks', '')}",
            f"**Trade-offs:** {policy.get('trade_offs', '')}",
            f"**Conditions:** {policy.get('conditions', '')}",
            f"**Evidence basis:** {policy.get('evidence_basis', '')}",
        ]

    # Preserve both sides of any disagreement found during analysis.
    lines += ["## Conflicts and agreements"]
    for conflict in conflicts.get("conflicts", []):
        lines += [
            f"### Conflict: {conflict.get('lens_a', '')} ↔ {conflict.get('lens_b', '')}",
            f"- {conflict.get('lens_a', '')}: {conflict.get('finding_a', '')}",
            f"- {conflict.get('lens_b', '')}: {conflict.get('finding_b', '')}",
            f"- **Implication:** {conflict.get('implication', '')}",
        ]
    if not conflicts.get("conflicts"):
        lines.append("No material disagreement was identified in the saved analysis; see the note below for unresolved tensions.")

    # Finish with the recommendation, conditions, and verification notes.
    lines += [
        "",
        "**Agreements:** " + "; ".join(conflicts.get("agreements", [])),
        "",
        "## Conditional recommendation",
        recommendation.get("recommendation", ""),
        "",
        recommendation.get("why", ""),
        "",
        "### Conditions",
    ]
    conditions = recommendation.get("conditions", [])
    lines += [f"- {item}" for item in conditions] or [
        "- Validate local enforcement capacity and due-process safeguards before implementation."
    ]

    lines += ["", "### What could change this recommendation"]
    changes = recommendation.get("what_would_change_this", [])
    lines += [f"- {item}" for item in changes] or [
        "- Better local outcome, cost and compliance data."
    ]

    lines += ["", "### Limitations"]
    lines += [f"- {item}" for item in recommendation.get("limitations", [])]
    lines += [
        "",
        "## Sources and verification",
        "The supplied assignment brief is the source for the article context in the prompt. Research findings should provide their own source URLs; no claim of live browsing is made. Verify primary sources and local legal requirements before relying on this report.",
        "",
    ]
    return "\n".join(lines)
