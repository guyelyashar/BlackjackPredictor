# AGENTS.md

## Project overview

BlackjackPredictor is an early-stage Flask application that estimates blackjack outcomes with a Monte Carlo simulation.

- `app/app.py` — Flask entry point and HTTP/form handling
- `app/deck.py` — deck construction and card operations
- `app/predictor.py` — hand evaluation, basic strategy, and simulation
- `app/templates/index.html` — Jinja page template
- `app/static/js/script.js` — browser-side behavior
- `app/static/css/input.css` — Tailwind source CSS
- `app/static/css/output.css` — generated Tailwind output
- `app/static/css/style.css` — handwritten styles
- `.agents/skills/` — local engineering workflow skills

This project is unfinished. Preserve its current behavior unless a task explicitly asks for a behavior change, and distinguish pre-existing defects from regressions caused by your work.

## Working principles

1. Read `.agents/skills/using-agent-skills/SKILL.md` at the start of a task and apply only the local skills relevant to that task.
2. State material assumptions before non-trivial implementation. If requirements conflict with the code, stop and ask which should take precedence.
3. Keep changes focused. Do not refactor adjacent code, rewrite comments, or add features outside the request.
4. Prefer small, explicit functions and standard-library solutions over new abstractions or dependencies.
5. Never edit dependencies under `node_modules/`, caches under `__pycache__/`, `.DS_Store` files, or other generated/vendor artifacts.
6. Do not claim success until the relevant verification commands pass. Report pre-existing failures separately.

## Setup and common commands

Run commands from the repository root unless noted otherwise.

### Python application

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install Flask pytest
```

`requirements.txt` is currently empty, so the final command supplies the app and test runner for local development. If dependency setup is in scope, record these dependencies in the project manifest instead of relying on the local-only install.

Run the app:

```bash
python app/app.py
```

The development server normally listens at `http://127.0.0.1:5000`.

### Frontend assets

Install pinned Node dependencies:

```bash
npm ci
```

Build Tailwind CSS:

```bash
npx @tailwindcss/cli -i app/static/css/input.css -o app/static/css/output.css
```

For active UI work, add `--watch` to the Tailwind command. Treat `output.css` as generated: change `input.css`, template classes, or Tailwind configuration and then rebuild it.

## Architecture and domain rules

- Keep request parsing and response rendering in `app/app.py`.
- Keep deck state and card primitives in `app/deck.py`.
- Keep blackjack rules, strategy decisions, and simulation orchestration in `app/predictor.py`.
- Use the canonical card names already used by the Python code: `Two` through `Ten`, `Jack`, `Queen`, `King`, and `Ace`.
- Preserve type hints on Python functions and important local variables.
- Avoid shared mutable simulation state. A prediction must start from a fresh shoe derived from `num_of_decks`; repeated requests must not silently accumulate decks or removed cards.
- A simulated round must not mutate the caller's hand or leak deck mutations into another round. Copy inputs/state at explicit simulation boundaries.
- When changing blackjack behavior, document the rule assumptions that affect results, such as dealer soft-17 behavior, blackjack payout, ties/pushes, splitting, doubling, and the treatment of other players' hidden cards.
- Monte Carlo tests must be deterministic. Inject or seed randomness in tests rather than asserting against an uncontrolled random run.
- Validate deck and hand sizes before drawing cards. Do not conceal impossible states with broad exception handling.
- Keep the simulation count configurable at an internal boundary when working on predictor code so tests can run quickly while production estimates can use a larger sample.

## Flask and frontend conventions

- Use form field names consistently across the template and `request.form`; do not use human-readable labels as backend keys.
- Validate all user-controlled values on the server even when the HTML input constrains them.
- Return clear `4xx` responses or field-level errors for invalid input; do not silently reinterpret malformed card data.
- Generate asset URLs with Jinja's `url_for('static', filename=...)`.
- Keep JavaScript class names in `PascalCase` and ordinary variables/functions in `camelCase`.
- Custom element names must remain lowercase and contain a hyphen.
- Preserve semantic labels, keyboard interaction, focus states, and sufficient color contrast in UI changes.
- Do not place a form inside another form. A single prediction submission should have one clear submit path.

## Tests and verification

There is currently no committed automated test suite. New or changed behavior should add focused tests under `tests/`, using `pytest` unless the project adopts another runner.

Minimum checks for every Python change:

```bash
python -m compileall -q app
pytest -q
```

If no tests exist yet, say so explicitly; do not present a missing test suite as a passing test run. At minimum, add tests for changed pure logic in `Deck` or `Predictor`.

For Flask changes, exercise the affected route with Flask's test client. Verify both valid and invalid inputs and assert response status plus meaningful response content.

For frontend changes:

```bash
npx @tailwindcss/cli -i app/static/css/input.css -o app/static/css/output.css
```

Then run the Flask app and inspect the affected flow in a browser at desktop and narrow viewport widths. Check the browser console for JavaScript, network, and template-loading errors.

Before handing off, review the diff and confirm that generated, cache, and vendor files were not changed unintentionally.

## High-value test cases

When touching the game engine, cover at least the relevant cases below:

- a fresh deck contains 52 cards and the correct rank multiplicities;
- multi-deck shoes contain exactly `52 * num_of_decks` cards;
- aces are valued as 11 when safe and downgraded to 1 as needed;
- hard, soft, pair, blackjack, bust, dealer bust, and push outcomes;
- split and double-down branches, including the exact cards consumed;
- repeated predictor calls are independent;
- known-card removal is reflected in the simulated shoe;
- seeded simulations produce repeatable results within the valid `0..100` percentage range;
- invalid deck counts, player counts, and card names are rejected at the HTTP boundary.

## Dependency and repository hygiene

- Add Python packages to `requirements.txt` with an intentional version policy.
- Add JavaScript packages through npm and commit matching `package.json` and `package-lock.json` changes.
- Do not commit `.venv/`, `node_modules/`, `__pycache__/`, `.pytest_cache/`, coverage output, or OS metadata.
- Do not hand-edit `package-lock.json` or `skills-lock.json`.
- Do not commit secrets, Flask secret keys, credentials, or local environment values. Use environment variables and document newly required variables.

## Completion report

When finishing a task, summarize:

1. the behavior changed;
2. the files changed;
3. the exact verification performed and its result;
4. any known limitation, pre-existing failure, or follow-up work.
