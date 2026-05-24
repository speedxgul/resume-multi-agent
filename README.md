# Resume Agent

Multi-agent resume updater CLI built with **LangGraph** and **Claude**. It pulls fresh data from your GitHub, pasted LinkedIn/Twitter text, manual notes, and arbitrary URLs, merges that with your existing PDF resume, lets you review section-by-section, then renders a new **LaTeX + PDF**.

## Architecture

```mermaid
flowchart LR
  PDF[Current resume PDF] --> Extract
  GH[GitHub API] --> Collectors
  LI[LinkedIn paste] --> Collectors
  TW[Twitter paste] --> Collectors
  MC[Manual context] --> Collectors
  URL[URL fetcher] --> Collectors
  Collectors --> Synth[Synthesizer agent]
  Extract --> Synth
  Synth --> Review[Human review CLI]
  Review --> Render[LaTeX renderer]
  Render --> Out[resume.tex / resume.pdf / resume.json]
```



**Agents (LangGraph nodes):**


| Agent                 | Role                                                 |
| --------------------- | ---------------------------------------------------- |
| GitHub collector      | Repos, stars, languages, README excerpts             |
| LinkedIn loader       | Reads pasted profile text                            |
| Twitter loader        | Reads pasted bio / pinned tweets                     |
| Manual context loader | Hackathon wins, recent work, free-form notes         |
| URL fetcher           | Fetches project pages, Devpost, blogs                |
| Synthesizer           | Claude merges everything into structured JSON resume |


## Quick start

```bash
# 1. Create virtualenv and install deps
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure secrets
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY (required)
# Optional: GITHUB_TOKEN for higher rate limits

# 3. Fill config + input files
python -m src.main init-inputs
# Edit config.yaml — name, email, github_username, links
# Put your current resume at inputs/resume.pdf
# Paste LinkedIn/Twitter text into inputs/*.txt
# Add hackathon wins / context to inputs/manual_context.md
# Add URLs to inputs/urls.txt

# 4. Run
python -m src.main update
```

## Commands

```bash
# Full pipeline with interactive review (default)
python -m src.main update

# Custom PDF path
python -m src.main update --pdf ~/Downloads/my_resume.pdf

# Skip human review (accept all synthesizer changes)
python -m src.main update --skip-review

# Skip PDF compilation (only .tex + .json)
python -m src.main update --no-compile

# Create starter input files
python -m src.main init-inputs
```

## Interactive review (feedback loop)

After synthesis, each section is reviewed in order: `summary`, `experience`, `projects`, `skills`, `education`, `achievements`.

For every section you can:


| Key   | Action                                                                                          |
| ----- | ----------------------------------------------------------------------------------------------- |
| **y** | Accept the proposed version                                                                     |
| **n** | Keep the previous/current version                                                               |
| **f** | Press **f** then Enter, then type feedback on the next prompt (arrow keys work there) |


You can press **f** multiple times on the same section until you're happy, then **y** to accept and move on.

Example feedback:

- *"Shorten to 2 lines and mention hackathon wins"*
- *"Make the LeadPool bullet highlight Zircuit track prize"*
- *"Move Rust to the top of Languages"*

Section revisions use `models.extractor` (default: Claude Sonnet). Optional config: `revise_max_tokens` (default `4096`).

## Outputs

After a successful run, check `outputs/`:


| File                | Description                                   |
| ------------------- | --------------------------------------------- |
| `resume.draft.json` | Raw synthesizer output (pre-review)           |
| `resume.json`       | Final approved structured resume              |
| `resume.tex`        | LaTeX source                                  |
| `resume.pdf`        | Compiled PDF (needs `tectonic` or `pdflatex`) |


## PDF compilation

Install one of:

- [Tectonic](https://tectonic-typesetting.github.io/) (recommended, single binary)
- TeX Live (`pdflatex`)

If neither is installed, you'll still get `.tex` and `.json`.

## LinkedIn / Twitter (no scraping)

LinkedIn and Twitter don't have reliable public APIs for profile scraping. Instead:

1. Open your profile in the browser
2. Select all relevant text (Experience, About, etc.)
3. Paste into `inputs/linkedin_profile.txt` or `inputs/twitter_profile.txt`

The synthesizer treats this as first-class source data.

## Links in manual_context.md

Any `http(s)://` URL you write in `inputs/manual_context.md` is **automatically extracted and fetched** (markdown links and bare URLs both work). You do not need to duplicate them in `urls.txt`.


| Link type                                | Behavior                                                  |
| ---------------------------------------- | --------------------------------------------------------- |
| **GitHub repo** (`github.com/user/repo`) | README fetched via GitHub API                             |
| **Devpost / project pages**              | Page text extracted via HTTP                              |
| **X / Twitter**                          | Not fetched (kept as reference links for the synthesizer) |


URLs already listed in `urls.txt` are skipped when fetching from manual context to avoid duplicate requests.

Example in `manual_context.md`:

```markdown
## Hackathon wins
- EthVietnam 2025 — [leadpool](https://github.com/you/leadpool) — Devpost: https://devpost.com/software/leadpool
```

## Config reference

See `config.yaml` for all options. Key fields:

```yaml
profile:
  name: "Your Name"
  email: "you@example.com"
  github: "yourusername"   # or full URL
  linkedin: "https://linkedin.com/in/you"

sources:
  github_username: "yourusername"
  manual_context_file: "inputs/manual_context.md"
  urls_file: "inputs/urls.txt"
```

## What to give the agent

For best results, provide:

1. **Current resume PDF** — baseline structure and older facts
2. **GitHub username** — auto-fetches repos and READMEs
3. **LinkedIn paste** — jobs, education, about
4. **Manual context** — hackathon wins, metrics, recent projects; paste GitHub/Devpost links inline (auto-fetched)
5. **URLs** (optional) — extra pages in `urls.txt` if not already in manual context

## License

MIT