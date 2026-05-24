"""Canonical resume schema. Synthesizer outputs this; renderer consumes it."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator

# Body sections in default PDF order (contact stays in header).
DEFAULT_SECTION_ORDER: list[str] = [
    "summary",
    "experience",
    "projects",
    "skills",
    "education",
    "achievements",
]

# Human review / shell edit order (may differ from PDF order).
REVIEWABLE_SECTIONS: list[str] = [
    "summary",
    "education",
    "experience",
    "projects",
    "skills",
    "achievements",
]


def normalize_section_order(order: list[str] | None) -> list[str]:
    """Ensure section_order contains each body section exactly once."""
    if not order:
        return list(DEFAULT_SECTION_ORDER)

    seen: list[str] = []
    for name in order:
        if name in DEFAULT_SECTION_ORDER and name not in seen:
            seen.append(name)
    for name in DEFAULT_SECTION_ORDER:
        if name not in seen:
            seen.append(name)
    return seen


class Contact(BaseModel):
    name: str
    email: str
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None
    twitter: str | None = None
    website: str | None = None


class Experience(BaseModel):
    company: str
    role: str
    location: str | None = None
    start_date: str = Field(description="e.g. 'May 2024' or '2024-05'")
    end_date: str | None = Field(default=None, description="None or empty means 'Present'")
    bullets: list[str] = Field(default_factory=list)


class Project(BaseModel):
    name: str
    description: str = ""
    tech: list[str] = Field(default_factory=list)
    link: str | None = None
    bullets: list[str] = Field(default_factory=list)


class Education(BaseModel):
    institution: str
    degree: str
    field: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None
    coursework: list[str] = Field(default_factory=list)


class Achievement(BaseModel):
    title: str
    description: str | None = None
    date: str | None = None
    link: str | None = None


class Resume(BaseModel):
    """Full resume payload. Sections may be empty lists if a person has none."""

    contact: Contact
    section_order: list[str] = Field(
        default_factory=lambda: list(DEFAULT_SECTION_ORDER),
        description="Order of body sections in the PDF (summary, experience, projects, skills, education, achievements)",
    )
    summary: str | None = None
    experience: list[Experience] = Field(default_factory=list)
    projects: list[Project] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    skills: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Grouped skills, e.g. {'Languages': ['Python','Go'], 'ML': ['PyTorch']}",
    )
    achievements: list[Achievement] = Field(default_factory=list)

    @field_validator("section_order", mode="before")
    @classmethod
    def _normalize_order(cls, value: list[str] | None) -> list[str]:
        return normalize_section_order(value)

    def section_payload(self, name: str) -> Any:
        """Return the value of a top-level section by name (for diff/review UI)."""
        if name == "section_order":
            return self.section_order
        return getattr(self, name)
