# Inputs Guide

All input files live in the `inputs/` folder. Run `python -m src.main init-inputs` to create blank starter versions.

> Example versions of every file are in `inputs/examples/` — copy and adapt them.

---

## `inputs/resume.pdf` (required)

Your **current** resume as a PDF. This is the baseline:

- Text is extracted and passed to the synthesizer as context ("existing resume text")
- Dates, titles, and structure from your old resume help Claude avoid regressions
- If you don't have a PDF yet, create a simple one-page doc and save it as PDF

**Tips:**
- The PDF must be text-based (not a scanned image). Most Word/Google Docs exports are fine.
- Searchable PDFs are best — text extraction works better the more text layers the PDF has.
- You can pass a different path with `--pdf ~/path/to/resume.pdf`

---

## `inputs/manual_context.md` (most important)

Free-form markdown notes about your work. **This is where you put everything that doesn't fit elsewhere** — hackathon wins, side projects, recent work, metrics, awards.

**Any `http(s)://` URL you write here is automatically fetched:**

| URL type | What gets fetched |
|----------|------------------|
| `github.com/user/repo` | README (via GitHub API, up to 8 000 chars) |
| Devpost, project pages | Page text extracted via HTTP |
| X / Twitter | Kept as a reference link only — not fetched |

You do **not** need to duplicate URLs in `urls.txt` if you've already added them here.

### Structure

```markdown
## Recent work / projects
- https://github.com/you/project-alpha
- https://github.com/you/project-beta (ongoing)

## Hackathon wins
- ETHGlobal Bangkok 2024 — DeFi Track Winner $2 000 — built [SettleStream](https://github.com/you/settlestream)
  Devpost: https://devpost.com/software/settlestream

- Solana Breakpoint 2024 — Infrastructure Track Runner-up $1 000 — built [BatchSettler](https://github.com/you/batch-settler)

## Achievements / awards
- $10k+ won in hackathons and protocol grants
- Speaker at DevConnect Istanbul 2024 — talk: https://youtu.be/example-talk-id

## Anything else the agent should know
- Currently learning Rust and ZK proofs
- Open to remote roles, preferably DeFi / infra
```

### Tips

- Write in any order — the synthesizer reads all of it
- Include GitHub links for projects you want on the resume; the README will be fetched and used to write project bullets
- Metrics and prize amounts are especially valuable (`$2 250`, `500k subscribers`, `reduced latency 40%`)
- Don't worry about formatting — it's fed as raw text to Claude

---

## `inputs/linkedin_profile.txt`

Paste the raw text of your LinkedIn profile here. No login, no API — just copy-paste from your browser.

### How to copy your LinkedIn text

1. Open [linkedin.com](https://linkedin.com) → your profile
2. Click the **About** section, click **See more** to expand everything
3. Scroll down through Experience, Education, Skills, Certifications
4. Select all relevant sections (`Cmd+A` on the page won't work — select section by section)
5. Paste into this file

### What to include

- **About / Summary** — bio paragraph
- **Experience** — each role with title, company, dates, description
- **Education** — degree, institution, dates, relevant coursework
- **Skills** — your listed skills
- **Certifications** — if relevant

### Example snippet

```text
About
Senior software engineer focused on distributed systems and DeFi infrastructure.
Built scalable trading systems handling $50M+ daily volume.

Experience

Senior Backend Engineer · Acme Protocol
Jan 2023 – Present · Remote

- Designed and built the core settlement layer, reducing finality time from 8s to 1.2s
- Led migration from monolith to microservices (Go + gRPC), improving P99 latency 40%
- Mentored 3 junior engineers

Software Engineer · Big Tech Co
Jun 2021 – Dec 2022 · San Francisco, CA

- ...
```

---

## `inputs/twitter_profile.txt`

Paste your Twitter/X bio and any pinned tweets or notable threads here. Useful for:
- Personal brand / summary statement
- Announcements of projects (often have good one-liner descriptions)
- Links to articles or talks

### Example

```text
Building in DeFi and ZK space. Web3 infra, trading bots, hackathon wins.
Core contributor at @SomeProtocol.

Pinned tweet:
Just won DeFi track at ETHGlobal Bangkok with SettleStream — permissionless batch auction settlement.
Full writeup: https://mirror.xyz/...
```

---

## `inputs/urls.txt`

One URL per line — extra pages to fetch. Use this for links that aren't already in `manual_context.md`.

```text
# One URL per line
# Lines starting with # are ignored

https://devpost.com/software/settlestream
https://mirror.xyz/youraddress/article-slug
https://youtu.be/videoID
https://yoursite.dev/projects
```

**Deduplication:** URLs already in `manual_context.md` are automatically skipped here to avoid fetching twice.

**Supported:**
- Devpost project pages
- Blog posts (Mirror, Substack, Medium, personal sites)
- YouTube (page title + description are fetched, not transcript)
- Any public HTTP page with readable text content

**Skipped:**
- Twitter/X (kept as reference only)
- Binary files, PDFs, non-HTML content

---

## GitHub collection (via `config.yaml`)

The GitHub collector is separate from the URL fetcher. It scans **all your public repos** when you set `github_username` in `config.yaml`:

```yaml
sources:
  github_username: "yourusername"   # enables bulk GitHub collection
  github_max_repos: 30              # cap on repos (sorted by stars + recency)
  github_include_readmes: 5         # fetch READMEs for top N repos
```

**What it collects per repo:**
- Name, description, URL, homepage
- Primary language + full language breakdown
- Topics / tags
- Stars, forks, last push date
- README excerpt (first 4 000 chars, top `github_include_readmes` repos only)

**Without `github_username`:** Only repos you explicitly link in `manual_context.md` or `urls.txt` are fetched (via README API).

**With `GITHUB_TOKEN` set in `.env`:** Higher API rate limits (5 000/hour vs 60/hour unauthenticated); also enables private repo access if the token has `repo` scope.

---

## Priority and conflicts

When the synthesizer sees conflicting information (e.g. different dates for the same job in your PDF vs LinkedIn paste), it follows this priority:

1. `profile:` block in `config.yaml` — **always wins** for contact info
2. Fresh sources (LinkedIn, manual context, GitHub, URLs) — preferred over old PDF text for facts
3. Existing PDF text — used as baseline structure and for anything not covered by other sources

You can always correct mistakes during interactive review or in the edit shell.
