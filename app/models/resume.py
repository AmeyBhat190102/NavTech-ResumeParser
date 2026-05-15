from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


# ── Sub-schemas ────────────────────────────────────────────────────────────────

class ContactInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    website: Optional[str] = None


class EducationEntry(BaseModel):
    institution: str
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    graduation_year: Optional[str] = None
    gpa: Optional[str] = None


class ExperienceEntry(BaseModel):
    company: str
    position: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None          # "Present" if current
    duration: Optional[str] = None          # e.g. "2 years 3 months"
    description: Optional[list[str]] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: Optional[list[str]] = Field(default_factory=list)
    url: Optional[str] = None


class CertificationEntry(BaseModel):
    name: str
    issuer: Optional[str] = None
    date: Optional[str] = None
    url: Optional[str] = None


# ── Root schema ────────────────────────────────────────────────────────────────

class ParsedResume(BaseModel):
    contact: Optional[ContactInfo] = None
    summary: Optional[str] = None
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    raw_text_length: Optional[int] = None   # metadata: chars in source text
    strategy_used: Optional[str] = None     # which strategy produced this
