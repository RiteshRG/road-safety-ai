# Agent implementation rules

- Build a three-hour academic decision-support prototype, not a general chatbot or production policy platform.
- Keep the workflow in this order: research lenses → policy options → transparent trade-off scoring → conflict report → conditional recommendation.
- Research responsibilities must be distinct. The model is not a live search tool; never claim browsing, fabricate source URLs, statistics, legal rules or effects, or treat model output as verified evidence.
- Use Groq through environment-provided credentials. Never persist, print or include API keys in prompts, artifacts, reports or commits.
- Treat persistent files as the source of truth for progress. Reuse only complete, parseable artifacts in the matching scenario-hash run directory.
- Persist each successful stage atomically before starting the next. On rate limit/failure, preserve progress and exit without endless retries.
- Scores are deterministic Python arithmetic over explicit provisional ratings. Disclose the formula, ratings and limitations; do not present scores as empirical estimates.
- Surface disagreements and policy trade-offs explicitly. Recommendations must state conditions and what evidence could change them.
- Keep dependencies minimal, modules small, errors actionable, and setup instructions runnable from the repository root.
