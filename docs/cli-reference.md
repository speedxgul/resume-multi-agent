# CLI Reference

All commands are run as:

```bash
python -m src.main <command> [options]
```

Run `python -m src.main --help` or `python -m src.main <command> --help` to see help in your terminal.

---

## `update`

Run the full pipeline: collect sources → synthesize → review → render.

```bash
python -m src.main update [OPTIONS]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--pdf PATH` | `inputs/resume.pdf` | Path to your current resume PDF |
| `--config PATH` | `config.yaml` | Path to config file |
| `--skip-review` | `false` | Accept all synthesizer changes without interactive review |
| `--no-compile` | `false` | Write `.tex` and `.json` only; skip PDF compilation |
| `--interactive` / `-i` | `false` | After rendering, drop straight into the edit shell |

### Examples

```bash
# Standard run
python -m src.main update

# Custom PDF location
python -m src.main update --pdf ~/Downloads/my_resume.pdf

# Skip the review step (accept everything)
python -m src.main update --skip-review

# Generate outputs but don't compile PDF yet
python -m src.main update --no-compile

# Full pipeline, then immediately open the edit shell
python -m src.main update --interactive
python -m src.main update -i

# Custom config file
python -m src.main update --config configs/work.yaml
```

### What it does

1. Extracts text from the resume PDF
2. Runs five collectors in parallel (GitHub, LinkedIn, Twitter, manual context, URLs)
3. Calls Claude Opus to synthesize everything into structured resume JSON → `outputs/resume.draft.json`
4. Runs interactive review (unless `--skip-review`)
5. Writes `outputs/resume.json`, `outputs/resume.tex`
6. Compiles `outputs/resume.pdf` (unless `--no-compile` or `output.compile_pdf: false` in config)

---

## `shell`

Open the interactive edit shell on an existing resume. Use this after `update` when you want to keep tweaking without re-running the full pipeline.

```bash
python -m src.main shell [OPTIONS]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--config PATH` | `config.yaml` | Path to config file |
| `--json PATH` | `outputs/resume.json` | Resume JSON to load |

### Examples

```bash
# Open shell on the default resume
python -m src.main shell

# Open on a different JSON file
python -m src.main shell --json outputs/resume_v2.json
```

See [Edit Shell Reference](edit-shell.md) for all shell commands.

---

## `render`

Reload `outputs/resume.json` from disk and regenerate `.tex` and `.pdf`. Use this after manually editing the JSON in your editor.

```bash
python -m src.main render [OPTIONS]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--config PATH` | `config.yaml` | Path to config file |
| `--json PATH` | `outputs/resume.json` | Resume JSON to render |
| `--no-compile` | `false` | Write `.tex` only; skip PDF compilation |
| `--open` | `false` | Open the PDF in your default viewer after rendering |

### Examples

```bash
# Regenerate tex + PDF
python -m src.main render

# Regenerate and open PDF immediately
python -m src.main render --open

# Regenerate tex only (no PDF compilation)
python -m src.main render --no-compile

# Render from a specific JSON file
python -m src.main render --json outputs/backup.json
```

---

## `compile`

Compile an existing `outputs/resume.tex` to PDF. No Claude calls — just LaTeX. Use this when you've edited the `.tex` file directly.

```bash
python -m src.main compile [OPTIONS]
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--config PATH` | `config.yaml` | Path to config file |
| `--open` | `false` | Open the PDF after compiling |

### Examples

```bash
# Compile to PDF
python -m src.main compile

# Compile and open
python -m src.main compile --open
```

---

## `init-inputs`

Create blank starter input files under `inputs/`. Safe to run multiple times — it will not overwrite files that already exist.

```bash
python -m src.main init-inputs
```

Creates (if not already present):

- `inputs/manual_context.md`
- `inputs/linkedin_profile.txt`
- `inputs/twitter_profile.txt`
- `inputs/urls.txt`

> Does **not** create `inputs/resume.pdf` — you must supply your own PDF.

---

## Summary Table

| Command | What it does | Claude? | LaTeX? |
|---------|-------------|---------|--------|
| `update` | Full pipeline | Yes (Opus + Sonnet) | Yes (optional) |
| `shell` | Interactive edits | On demand | On demand |
| `render` | JSON → .tex → PDF | No | Yes (optional) |
| `compile` | .tex → PDF | No | Yes |
| `init-inputs` | Create starter files | No | No |

---

## Environment Variables

These are read from `.env` (via `python-dotenv`) at startup:

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Claude API key |
| `GITHUB_TOKEN` | No | GitHub PAT — higher rate limits; needed for private repos |
| `RESUME_AGENT_SYNTHESIZER_MODEL` | No | Override synthesizer model (default: `claude-opus-4-7`) |
| `RESUME_AGENT_EXTRACTOR_MODEL` | No | Override reviser model (default: `claude-sonnet-4-5`) |

All overrides can also be set in `config.yaml` under `models:`.
