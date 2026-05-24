# Edit Shell Reference

The edit shell is an interactive REPL that lets you iterate on your resume **without re-running the full pipeline**. Open it after `update` finishes, or any time you want to tweak the PDF.

```bash
# Open on the default outputs/resume.json
python -m src.main shell

# Or jump straight into it after update
python -m src.main update --interactive
python -m src.main update -i
```

You'll see:

```
Edit mode — type help for commands
Loaded outputs/resume.json

>
```

---

## All Commands

### `help`
Show the command reference.

```
> help
```

---

### `pdf` / `compile`
Compile `outputs/resume.tex` → `outputs/resume.pdf`. Run this after any edit to refresh the PDF.

```
> pdf
Compiled: outputs/resume.pdf
```

---

### `open`
Open the PDF in your system viewer (Preview on macOS, Evince on Linux, Adobe on Windows).

```
> open
```

---

### `order`
Show the current PDF section block order (top to bottom).

```
> order
PDF section order (top → bottom):

  1. summary
  2. experience
  3. projects
  4. skills
  5. education
  6. achievements

Use `move education above experience` to reorder blocks instantly.
```

---

### `show [section]`

Show the current content of a section as JSON. Reloads from disk first so you always see the latest saved state.

```
> show                   # overview table — all sections
> show contact
> show summary
> show experience
> show projects
> show skills
> show education
> show achievements
> show order             # same as `order`
```

---

### `reload`
Reload `outputs/resume.json` from disk into memory. Use this after making manual edits to the file in your editor.

```
> reload
Reloaded outputs/resume.json
```

---

### `move <section> above|below <section>`

Instantly reorder whole section blocks in the PDF. No Claude call — the change is written to disk immediately.

```
> move education above experience
> move skills below projects
> move achievements above education
```

**Available section names:** `summary`, `experience`, `projects`, `skills`, `education`, `achievements`

Short aliases also work: `edu`, `exp`, `project`, `skill`, `achievement`

After moving, run `pdf` to rebuild the PDF.

```
> move education above experience
Updated section order:
  1. summary
  2. education
  3. experience
  4. projects
  5. skills
  6. achievements
Saved outputs/resume.json and outputs/resume.tex
Run `pdf` to refresh the PDF.
```

---

### `edit <section>`

Revise a specific section using natural-language feedback sent to Claude. You'll be shown a diff and asked to confirm before anything is saved.

```
> edit summary
> edit experience
> edit projects
> edit skills
> edit education
> edit achievements
> edit order          # reorder sections via Claude (use `move` for instant reorder)
```

After running:
1. You're prompted for feedback
2. Claude revises the section
3. The diff is shown
4. You confirm with `y` or discard with `n`

**Example session:**

```
> edit experience
Feedback: shorten the Acme Corp bullets to 2 per job, add metrics where possible

  [diff shown here]

Apply changes? [Y/n]: y
Saved outputs/resume.json and outputs/resume.tex
Run `pdf` to refresh the PDF.
```

**Example feedback phrases:**
- `"Shorten summary to 2 sentences, keep the hackathon wins"`
- `"Add coursework: Distributed Systems, OS to education"`
- `"Move SettleStream to the top of projects"`
- `"Add a link: 'SettleStream' → https://github.com/you/settlestream in the first bullet"`
- `"Group skills into: Languages, Frameworks, Web3, Tools"`
- `"Reorder: put education right after summary"`

---

### `edit` (full resume)

Revise the entire resume at once with natural-language feedback. Shows diffs per section before asking you to confirm.

```
> edit
Feedback: tighten all bullets to one line each, add the $20k hackathon prize total to summary
```

This calls Claude with the full resume JSON. Good for cross-cutting changes. Use section-specific `edit <section>` for targeted changes (cheaper, faster).

---

### `save`

Reload `outputs/resume.json` from disk, then regenerate `outputs/resume.tex`. Use this after manually editing the JSON file in your code editor.

```
> save
Reloaded from disk and saved outputs/resume.json and outputs/resume.tex
```

Flow for manual edits:
```
1. Edit outputs/resume.json in your editor and save it
2. Switch back to the shell
3. > save
4. > pdf
```

---

### `quit` / `exit`

Exit the shell.

```
> quit
Goodbye.
```

---

## Inline Links

You can ask Claude to add clickable links anywhere in the resume by using markdown syntax in your feedback:

```
> edit projects
Feedback: Link "SettleStream" to https://github.com/you/settlestream in the first bullet
```

Claude will output: `Built [SettleStream](https://github.com/you/settlestream) for ETHGlobal Bangkok`

In the PDF, that renders as a proper `\href{}{}` hyperlink.

This works in **any text field** — summary, bullets, descriptions, project names, company names, skills.

---

## Auto-compile

By default you need to run `pdf` manually after edits. To compile automatically after every `edit`:

```yaml
# config.yaml
output:
  auto_compile_after_edit: true
```

---

## Full Example Session

```
$ python -m src.main shell

Edit mode — type help for commands
Loaded outputs/resume.json

> order
  1. summary
  2. experience
  3. projects
  4. skills
  5. education
  6. achievements

> move education above experience
Updated section order:
  1. summary
  2. education
  3. experience
  ...
Saved outputs/resume.json and outputs/resume.tex
Run `pdf` to refresh the PDF.

> pdf
Compiled: outputs/resume.pdf

> open

> edit summary
Feedback: mention $20k+ in hackathon wins, keep it to 2 lines

  [diff shown]

Apply changes? [Y/n]: y
Saved outputs/resume.json and outputs/resume.tex

> pdf
Compiled: outputs/resume.pdf

> edit experience
Feedback: for the Acme Protocol job, add a bullet about the MEV bot reducing slippage 15%

  [diff shown]

Apply changes? [Y/n]: y

> pdf
> open
> quit
Goodbye.
```

---

## Tips

- **Always run `pdf` after edits** to see your changes (unless `auto_compile_after_edit: true`).
- **`show <section>` before `edit <section>`** — see exactly what Claude is working from.
- **Edit `outputs/resume.json` directly** for bulk changes (dates, typos, exact wording), then `save` + `pdf`.
- **Section reordering:** use `move` for instant reorder; `edit order` for Claude-assisted complex reorders.
- **`n` at the confirm prompt discards cleanly** — nothing is written to disk.
