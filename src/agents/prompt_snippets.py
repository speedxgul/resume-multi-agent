"""Shared LLM prompt snippets for resume editing."""

LINK_GUIDANCE = """
Inline clickable links in PDF: use markdown [visible text](https://url) inside any text field
(summary, bullets, descriptions, titles, skills, company names, etc.).
Example: Built [SettleStream](https://github.com/user/settlestream) for ETHGlobal Bangkok 2024.
Do not use HTML. Plain URLs without markdown render as text only.
Project/achievement `link` fields still work as whole-item URLs (shown as "link" in PDF).
"""

REORDER_GUIDANCE = """
Reordering:
- Items within a section (jobs, projects, bullets): reorder the JSON array — first entry appears first.
  "2nd from bottom" in a list of N means index N-2 (0-based). "Bottom" means last index N-1.
- Resume section blocks (Summary, Experience, Projects, etc.): set `section_order` to the desired
  sequence using exactly these names: summary, experience, projects, skills, education, achievements.
  Example: ["summary", "education", "experience", "projects", "skills", "achievements"]
"""
