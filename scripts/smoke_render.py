"""Quick smoke test for renderer without LLM calls."""

from src.renderer import render_latex, write_outputs
from src.schema import Contact, Experience, Project, Resume

resume = Resume(
    contact=Contact(
        name="Jane Doe",
        email="jane@example.com",
        github="https://github.com/janedoe",
        location="San Francisco, CA",
    ),
    summary="Software engineer building developer tools.",
    experience=[
        Experience(
            company="Acme Corp",
            role="Software Engineer",
            start_date="Jan 2024",
            end_date="Present",
            bullets=["Built X improving Y by 40%"],
        )
    ],
    projects=[
        Project(
            name="resume-agent",
            description="Multi-agent resume updater",
            tech=["Python", "LangGraph"],
            link="https://github.com/janedoe/resume-agent",
            bullets=["Automated resume updates from GitHub and LinkedIn"],
        )
    ],
    skills={"Languages": ["Python", "Go"], "Tools": ["LangGraph", "Claude"]},
)

tex = render_latex(resume)
assert "\\documentclass" in tex
assert "Jane Doe" in tex

paths = write_outputs(resume, compile=False)
print("render ok:", paths)
