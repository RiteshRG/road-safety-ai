# Beyond the Licence

A small issue explainer about why stricter licensing alone may not reduce road deaths. It presents the article brief's figures, distinguishes test performance from real-road behaviour, visualizes enforcement steps, and lets visitors reason through three safety situations.

## Run

Serve the repository root: `python -m http.server 8000`, then open `http://localhost:8000/website/`. The JSON-driven sections need HTTP fetch and will not populate when opened as a `file://` URL.

## Content integrity

Figures and comparisons are stored in `data/*.json`. Article figures are attributed to the supplied assignment brief; they are not independently verified. The comparison deliberately avoids inferring that licence-test pass marks cause fatality outcomes. Scenarios teach general safe-driving reasoning and do not state jurisdiction-specific legal advice.

## Structure

`index.html`, `styles.css`, `app.js`, and `data/`. Feature specs, prompts, reviewer instructions, and the small design skill are under `.github/`.

## Reading the source

The JavaScript render functions describe their purpose, inputs, outputs, and actions in comments. The HTML and CSS identify each page section and explain its visual role. Start with `app.js`'s `startWebsite()` function to follow how JSON becomes page content.
