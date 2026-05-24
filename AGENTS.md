# AGENTS.md

## Cursor Cloud specific instructions

### Project overview

Resume Agent is a Python CLI tool (no web frontend/backend) that generates LaTeX/PDF resumes from multiple data sources via LangGraph + Claude. See `README.md` for architecture and commands.

### Running the application

- Activate the virtualenv first: `source .venv/bin/activate`
- All CLI commands: `python -m src.main --help`
- The `update` command requires `ANTHROPIC_API_KEY` and a resume PDF at `inputs/resume.pdf`.
- Commands that do **not** need an API key: `init-inputs`, `render`, `compile`.
- `render` and `compile` work on previously generated `outputs/resume.json` / `outputs/resume.tex`.

### Smoke tests

There is no pytest/unittest suite. The two smoke scripts in `scripts/` must be run with `PYTHONPATH=/workspace`:

```
PYTHONPATH=/workspace python scripts/smoke_render.py
PYTHONPATH=/workspace python scripts/test_url_extract.py
```

### Linting

No linter is configured in the repo. `ruff check src/ scripts/` works for ad-hoc linting (ruff is installed in the virtualenv). There is one pre-existing unused-import warning in `src/reviewer.py` (F401 for `Panel`).

### LaTeX / PDF compilation

`tectonic` is installed at `/usr/local/bin/tectonic`. The `compile` and `render` commands use it to build PDFs. If tectonic is missing, `.tex` and `.json` are still generated.

### Environment variables

- `ANTHROPIC_API_KEY` (required for `update` / `shell` / `edit` commands)
- `GITHUB_TOKEN` (optional, raises GitHub API rate limits)
- See `.env.example` for the full list.
