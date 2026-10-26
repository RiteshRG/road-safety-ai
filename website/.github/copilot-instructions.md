# Website implementation rules

- This is a three-hour academic prototype. Keep features small, explainable and independently reviewable.
- Treat the supplied “Sense & Licence” assignment brief as the article source of truth. Do not invent statistics, laws, penalties, causes, or country context.
- Identify article-derived figures in the data and UI. Keep assumptions and source limits visible; do not claim correlation proves causation.
- Keep neutral policy language and focus on the article's question: why do deaths rise despite stricter rules, and which enforcement-focused policies could help?
- Store repeatable content in `data/*.json`; keep presentation and interaction in separate files.
- Prefer small reusable functions and native browser features. Add no framework or dependency without a concrete need.
- Preserve this visual system: public-interest editorial tone, readable type, green/charcoal palette, restrained motion, responsive layout and keyboard-accessible controls.
- Validate data loading and each feature before extending scope. Record important limitations in the README.
