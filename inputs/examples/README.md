# Example Input Files

These are worked examples of every input file. Copy them to `inputs/` and fill in your own details.

```bash
cp inputs/examples/manual_context.md  inputs/manual_context.md
cp inputs/examples/linkedin_profile.txt  inputs/linkedin_profile.txt
cp inputs/examples/twitter_profile.txt  inputs/twitter_profile.txt
cp inputs/examples/urls.txt  inputs/urls.txt
```

Then put your resume PDF at `inputs/resume.pdf`.

See [docs/inputs-guide.md](../../docs/inputs-guide.md) for details on what to put in each file.

Optional: enable `sources.crustdata_enabled` and/or `target.enabled` in `config.yaml` for Crustdata MCP enrichment and job-targeted tailoring (see [config reference](../../docs/config-reference.md)).

| File | What it is |
|------|-----------|
| `manual_context.md` | Free-form notes, hackathon wins, project URLs (most important file) |
| `linkedin_profile.txt` | Copy-pasted text from your LinkedIn profile |
| `twitter_profile.txt` | Your Twitter/X bio and notable tweets |
| `urls.txt` | Extra URLs to fetch (Devpost, blogs, talks, project pages) |
