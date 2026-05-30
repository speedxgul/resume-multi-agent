# Config Reference

All configuration lives in `config.yaml` at the project root. It is loaded at startup by every `python -m src.main` command.

---

## Full annotated example

```yaml
# ─── Contact info ───────────────────────────────────────────────────────────
# These values always override whatever the synthesizer finds.
# Fill these in before your first run — they control the resume header.
profile:
  name: "Jane Doe"
  email: "jane@example.com"
  phone: "+1 555 000 0000"           # optional — omit or leave "" to hide
  location: "San Francisco, CA"      # optional
  linkedin: "https://linkedin.com/in/janedoe"
  github: "https://github.com/janedoe"   # full URL or just "janedoe"
  twitter: "https://x.com/janedoe"       # optional
  website: "https://janedoe.dev"          # optional

# ─── Source collectors ───────────────────────────────────────────────────────
sources:
  # GitHub bulk collector — set to your username to scan all public repos.
  # Leave empty "" to skip bulk scanning (only URLs you paste are fetched).
  github_username: "janedoe"

  # Max repos to analyze (sorted by stars + recency).
  github_max_repos: 30

  # Fetch full READMEs for the top N repos (heavier signal for the synthesizer).
  # Increase for richer project bullets; 0 to skip READMEs entirely.
  github_include_readmes: 5

  # Path to files with pasted LinkedIn / Twitter text.
  linkedin_profile_file: "inputs/linkedin_profile.txt"
  twitter_profile_file: "inputs/twitter_profile.txt"

  # Free-form notes + auto-fetched URLs. GitHub links here fetch READMEs.
  manual_context_file: "inputs/manual_context.md"

  # Extra URLs to fetch — one per line. Deduplicated against manual_context.md.
  urls_file: "inputs/urls.txt"

# ─── Models ──────────────────────────────────────────────────────────────────
models:
  # Full-resume synthesis (collect → merge). Opus recommended for best results.
  synthesizer: "claude-opus-4-7"

  # Per-section revisions during review and in the edit shell.
  # Sonnet is faster and cheaper for targeted edits.
  extractor: "claude-sonnet-4-5"

  # Max output tokens for the synthesizer (full resume JSON can be large).
  max_tokens: 13000

  # Max output tokens for per-section revisions.
  revise_max_tokens: 4096

# ─── Output ──────────────────────────────────────────────────────────────────
output:
  # Base name for output files.
  # With basename "resume": outputs/resume.json, resume.tex, resume.pdf
  resume_basename: "resume"

  # Compile PDF automatically after synthesis (during `update`).
  # Set false to skip compilation — useful if you don't have tectonic/pdflatex yet.
  compile_pdf: true

  # In the edit shell: recompile PDF automatically after every `edit` command.
  # Set true to avoid running `pdf` manually after each change.
  auto_compile_after_edit: false

  # Reserved for future use — cosmetic only in current template.
  font: "Latin Modern"
```

---

## Field reference

### `profile`

These fields populate the **resume header** (contact line). They are never changed by the synthesizer — what you put here is what appears on the resume, always.

| Field | Required | Notes |
|-------|----------|-------|
| `name` | Yes | Your full name |
| `email` | Yes | Your email address |
| `phone` | No | Include country code; omit to hide from resume |
| `location` | No | City, Country — shown in the header |
| `linkedin` | No | Full URL (`https://linkedin.com/in/...`) or leave blank |
| `github` | No | Full URL or just username (`janedoe`) |
| `twitter` | No | Full URL or handle (`@janedoe` or `https://x.com/janedoe`) |
| `website` | No | Personal site URL |

> After your first run, `contact.location` in `outputs/resume.json` controls what shows on the PDF — the JSON is the source of truth for subsequent `render` / `save` calls.

---

### `sources`

| Field | Default | Notes |
|-------|---------|-------|
| `github_username` | `""` | Set to your GitHub username to enable bulk repo scanning. Leave empty to skip. |
| `github_max_repos` | `30` | Caps the number of repos analyzed (sorted by stars + recency score) |
| `github_include_readmes` | `5` | Fetch READMEs for this many top repos. Higher = richer bullets but slower + more tokens |
| `linkedin_profile_file` | `inputs/linkedin_profile.txt` | Path to pasted LinkedIn text |
| `twitter_profile_file` | `inputs/twitter_profile.txt` | Path to pasted Twitter/X text |
| `manual_context_file` | `inputs/manual_context.md` | Path to manual notes; embedded URLs are auto-fetched |
| `urls_file` | `inputs/urls.txt` | Path to extra URLs file |
| `crustdata_enabled` | `false` | Enable Crustdata Person Enrich for structured LinkedIn data |
| `crustdata_profile_url` | `""` | Override profile URL; defaults to `profile.linkedin` |
| `crustdata_use_email` | `false` | Look up profile by `profile.email` when no LinkedIn URL is set |
| `crustdata_use_live` | `false` | Use live enrich endpoint (plan-gated; ~7 credits vs ~1 cached) |
| `crustdata_min_similarity_score` | `0.8` | Minimum match confidence for email reverse lookup |
| `crustdata_fields` | *(defaults)* | Optional list of Crustdata field sections to request |

**GitHub token:** Set `GITHUB_TOKEN` in `.env` for higher rate limits (5 000/hr vs 60/hr unauthenticated). Required for private repos (needs `repo` scope).

**Crustdata:** Set `CRUSTDATA_API_KEY` in `.env` and `crustdata_enabled: true` in config. Uses `profile.linkedin` by default (~1 credit per run for cached enrich). See [Crustdata pricing](https://docs.crustdata.com/general/pricing.md).

---

### `models`

| Field | Default | Notes |
|-------|---------|-------|
| `synthesizer` | `claude-opus-4-7` | Model for the full resume synthesis step |
| `extractor` | `claude-sonnet-4-5` | Model for section revisions (review + edit shell) |
| `max_tokens` | `13000` | Synthesizer output cap. Large resumes may need 10 000+ |
| `revise_max_tokens` | `4096` | Per-section revision output cap. Rarely needs changing. |

**Environment variable overrides** (useful for CI or testing):
```bash
RESUME_AGENT_SYNTHESIZER_MODEL=claude-opus-4-7
RESUME_AGENT_EXTRACTOR_MODEL=claude-sonnet-4-5
```

---

### `output`

| Field | Default | Notes |
|-------|---------|-------|
| `resume_basename` | `"resume"` | Output file stem. Change to `"jane_doe_resume"` to get `jane_doe_resume.pdf` |
| `compile_pdf` | `true` | Set `false` to skip LaTeX compilation during `update` |
| `auto_compile_after_edit` | `false` | Set `true` to compile PDF automatically after every edit shell `edit` command |
| `font` | `"Latin Modern"` | Reserved for future template variants |

---

## Multiple configs

You can maintain separate configs (e.g. one per target role) and switch with `--config`:

```bash
# configs/software_eng.yaml — tailored for backend roles
# configs/research.yaml — tailored for ML researcher roles

python -m src.main update --config configs/software_eng.yaml
python -m src.main shell --config configs/research.yaml
```

---

## Environment variables

Loaded from `.env` at startup (via `python-dotenv`). Environment variables take precedence over defaults.

| Variable | Notes |
|----------|-------|
| `ANTHROPIC_API_KEY` | **Required.** Your Anthropic key. |
| `GITHUB_TOKEN` | Optional. GitHub PAT for higher rate limits / private repos. |
| `RESUME_AGENT_SYNTHESIZER_MODEL` | Overrides `models.synthesizer` in config |
| `RESUME_AGENT_EXTRACTOR_MODEL` | Overrides `models.extractor` in config |

`.env` example:
```env
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
```
