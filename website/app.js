// SECTION: Shared data helpers
// Purpose: Keep loading JSON and formatting displayed numbers consistent.

/**
 * Purpose: Load one JSON data file from the website's data folder.
 * Input: name - the file name without the .json extension.
 * Output: A promise that resolves to the parsed JavaScript object or array.
 * What it does: Requests the file and gives a readable error if the request fails.
 */
async function readDataFile(name) {
  const response = await fetch(`data/${name}.json`);

  if (!response.ok) {
    throw new Error(`Could not load ${name} content`);
  }

  return response.json();
}

/**
 * Purpose: Format a number in the familiar Indian number style.
 * Input: value - a number to show in the page.
 * Output: A formatted string, such as "24,000".
 * What it does: Uses the browser's number formatter and allows one decimal place.
 */
function formatNumber(value) {
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 1,
  }).format(value);
}

// SECTION: Fatality trend
// Purpose: Present the two article figures and their percentage change.

/**
 * Purpose: Draw the reported road-death comparison.
 * Input: data - the contents of fatality_trend.json.
 * Output: None; updates the trend, hourly framing, and source elements in the page.
 * What it does: Calculates the percentage change and fills the trend display.
 */
function renderTrend(data) {
  const firstYearDeaths = data.deaths_lakh[0];
  const lastYearDeaths = data.deaths_lakh[1];
  const percentageChange = Math.round(
    ((lastYearDeaths / firstYearDeaths) - 1) * 100,
  );

  document.querySelector("#trend").innerHTML = `
    <div class="trend-year">
      <span>${data.years[0]}</span>
      <strong>${formatNumber(firstYearDeaths)}<small> lakh</small></strong>
      <span class="bar"><i style="width: 85%"></i></span>
    </div>
    <div class="trend-rise">
      <span>+${percentageChange}%</span>
      <i></i>
      <small>over the<br>reported period</small>
    </div>
    <div class="trend-year current">
      <span>${data.years[1]}</span>
      <strong>${formatNumber(lastYearDeaths)}<small> lakh</small></strong>
      <span class="bar"><i style="width: 100%"></i></span>
    </div>`;

  document.querySelector("#hourly").textContent = data.hourly_framing;
  document.querySelector("#trend-source").textContent = data.source;
}

// SECTION: Country comparison
// Purpose: Show only the comparisons and context supplied in the JSON data.

/**
 * Purpose: Draw India, Vietnam, and Singapore comparison rows.
 * Input: data - the contents of country_comparison.json.
 * Output: None; fills the country comparison list in the page.
 * What it does: Formats available fatality rates and clearly labels missing values.
 */
function renderCountries(data) {
  const countryRows = data.countries.map((country, index) => {
    let fatalityRate = "Not supplied";

    if (country.fatalities_per_lakh != null) {
      fatalityRate = `${formatNumber(country.fatalities_per_lakh)} <small>/ lakh</small>`;
    }

    return `
      <article class="country-row">
        <span class="country-number">0${index + 1}</span>
        <strong>${country.name}</strong>
        <div>
          <span class="country-value">${fatalityRate}</span>
          <span class="country-context">${country.licence_context}</span>
        </div>
        <p>${country.note}</p>
      </article>`;
  });

  document.querySelector("#countries").innerHTML = countryRows.join("");
}

// SECTION: Enforcement chain
// Purpose: Explain the steps between a rule and an actual consequence.

/**
 * Purpose: Draw the enforcement pipeline and unpaid e-challan figure.
 * Input: data - the contents of enforcement.json.
 * Output: None; fills the pipeline and statistic elements in the page.
 * What it does: Labels each pipeline step and highlights two possible weak links.
 */
function renderEnforcement(data) {
  const steps = data.steps.map((step, index) => {
    const isPotentialWeakLink = index === 2 || index === 4;
    const weakLinkClass = isPotentialWeakLink ? "weak" : "";
    const arrow = index < data.steps.length - 1 ? "<i>→</i>" : "";

    return `
      <div class="pipeline-step ${weakLinkClass}">
        <span>0${index + 1}</span>
        <strong>${step}</strong>
        ${arrow}
      </div>`;
  });

  document.querySelector("#pipeline").innerHTML = steps.join("");
  document.querySelector("#challans").textContent =
    `₹${formatNumber(data.unpaid_challans_crore)} crore`;
}

// SECTION: Beyond the Rule scenarios
// Purpose: Let visitors choose a safe response and understand the reasoning.

/**
 * Purpose: Create the scenario tabs, answer choices, and feedback.
 * Input: scenarios - the array of situations from scenarios.json.
 * Output: None; builds and updates the scenario interaction in the page.
 * What it does: Draws one situation at a time and responds when a choice is clicked.
 */
function renderScenarios(scenarios) {
  const tabs = document.querySelector("#scenario-tabs");
  const card = document.querySelector("#scenario-card");
  let activeScenarioIndex = 0;

  /**
   * Purpose: Draw the currently selected scenario.
   * Input: None; reads activeScenarioIndex and scenarios from the parent function.
   * Output: None; replaces the tab and scenario-card contents.
   * What it does: Adds click handlers so visitors can change scenarios or answer.
   */
  function drawScenario() {
    const scenario = scenarios[activeScenarioIndex];

    const tabButtons = scenarios.map((item, index) => `
      <button role="tab"
        aria-selected="${index === activeScenarioIndex}"
        data-index="${index}">
        <span>0${index + 1}</span>${item.category}<b>↗</b>
      </button>`);

    const answerButtons = scenario.options.map((option, index) => `
      <button class="option" data-option="${index}">
        <span>${String.fromCharCode(65 + index)}</span>${option}
      </button>`);

    tabs.innerHTML = tabButtons.join("");
    card.innerHTML = `
      <p class="eyebrow">${scenario.category.toUpperCase()} · SITUATION</p>
      <h3>${scenario.situation}</h3>
      <p class="scenario-question">${scenario.question}</p>
      <div class="options">${answerButtons.join("")}</div>
      <div class="feedback" hidden></div>`;

    tabs.querySelectorAll("button").forEach((button) => {
      button.addEventListener("click", () => {
        activeScenarioIndex = Number(button.dataset.index);
        drawScenario();
      });
    });

    card.querySelectorAll(".option").forEach((button) => {
      button.addEventListener("click", () => showAnswerFeedback(button, scenario, card));
    });
  }

  drawScenario();
}

/**
 * Purpose: Show whether an answer is safe and explain the reasoning.
 * Input: button - the selected answer; scenario - its data; card - its page element.
 * Output: None; disables choices, highlights the safe answer, and fills feedback.
 * What it does: Compares the selected option to the answer stored in the scenario.
 */
function showAnswerFeedback(button, scenario, card) {
  const selectedAnswer = Number(button.dataset.option);
  const selectedAnswerIsSafe = selectedAnswer === scenario.correct_option;
  const answerButtons = card.querySelectorAll(".option");

  answerButtons.forEach((answerButton) => {
    answerButton.disabled = true;

    if (Number(answerButton.dataset.option) === scenario.correct_option) {
      answerButton.classList.add("correct");
    }
  });

  if (!selectedAnswerIsSafe) {
    button.classList.add("incorrect");
  }

  const feedback = card.querySelector(".feedback");
  const responseMessage = selectedAnswerIsSafe
    ? "A safer choice."
    : "Pause and reconsider.";

  feedback.hidden = false;
  feedback.innerHTML = `
    <strong>${responseMessage}</strong>
    <p><b>Principle</b> ${scenario.principle}</p>
    <p><b>Risk</b> ${scenario.risk}</p>
    <p><b>Common mistake</b> ${scenario.common_mistake}</p>`;
}

// SECTION: Start the page
// Purpose: Load all content before drawing the data-driven sections.
// Input: Four JSON files in website/data/.
// Output: A populated page, or a visible message if a file cannot be loaded.

/**
 * Purpose: Load the page data and start the four data-driven sections.
 * Input: None; reads the four JSON files from website/data/.
 * Output: None; populates the page or shows a loading error message.
 * What it does: Waits for the data files, calls each renderer, and handles failure.
 */
async function startWebsite() {
  try {
    const [trend, countries, enforcement, scenarios] = await Promise.all([
      readDataFile("fatality_trend"),
      readDataFile("country_comparison"),
      readDataFile("enforcement"),
      readDataFile("scenarios"),
    ]);

    renderTrend(trend);
    renderCountries(countries);
    renderEnforcement(enforcement);
    renderScenarios(scenarios);
  } catch (error) {
    console.error(error);

    const errorMessage = document.createElement("p");
    errorMessage.className = "load-error";
    errorMessage.textContent =
      "Some explainer data could not be loaded. Run a local web server to view all sections.";
    document.querySelector("main").prepend(errorMessage);
  }
}

startWebsite();
