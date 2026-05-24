#!/usr/bin/env python3
from src.utils.richtext import render_richtext

assert "href" in render_richtext("See [LeadPool](https://github.com/u/LeadPool) here")
assert "LeadPool" in render_richtext("See [LeadPool](https://github.com/u/LeadPool) here")
assert render_richtext("plain text") == "plain text"
print("richtext ok")

from src.schema import Resume, Contact, normalize_section_order

order = normalize_section_order(["education", "summary", "experience"])
assert order[0] == "education"
assert len(order) == 6
print("section_order ok")

from src.renderer import render_latex

r = Resume(
    contact=Contact(name="T", email="t@t.com"),
    section_order=["summary", "education", "experience", "projects", "skills", "achievements"],
    summary="Built [app](https://example.com)",
)
tex = render_latex(r)
assert "\\href" in tex
assert "Education" in tex[:tex.find("Experience")] if "Experience" in tex else True
print("render ok")
