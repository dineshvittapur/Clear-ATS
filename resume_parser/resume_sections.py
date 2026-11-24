import re

# Canonical section names mapped to common heading variations
SECTION_HEADERS = {
    "summary": [
        "summary",
        "professional summary",
        "career objective",
        "objective",
        "profile",
        "about me",
    ],
    "skills": [
        "skills",
        "technical skills",
        "core competencies",
        "technologies",
        "tech stack",
        "tools & technologies",
        "key skills",
    ],
    "experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "internships",
        "internship",
        "internship experience",
        "work history",
    ],
    "projects": [
        "projects",
        "personal projects",
        "academic projects",
        "key projects",
        "notable projects",
    ],
    "education": [
        "education",
        "academic background",
        "educational qualifications",
        "academic qualifications",
        "qualifications",
    ],
    "certifications": [
        "certifications",
        "certificates",
        "licenses & certifications",
        "achievements",
        "awards",
    ],
}


def _match_section_header(line: str) -> str | None:
    """
    Checks if a line is a standalone section header.
    Returns the canonical section key if matched, else None.
    """
    # Remove trailing colons, dashes, or decorative characters
    normalized = re.sub(r"[:\-–—_|#]+$", "", line).strip().lower()

    # Section headers are short (usually 1 to 4 words)
    if len(normalized.split()) > 5 or len(normalized) > 45:
        return None

    for canonical_name, aliases in SECTION_HEADERS.items():
        if normalized in aliases:
            return canonical_name

    return None


def parse_resume_sections(resume_text: str) -> dict[str, str]:
    """
    Splits cleaned resume text into structured sections.
    Lines appearing before the first recognized header go into 'header' (contact/name).
    """
    sections: dict[str, list[str]] = {
        "header": [],
        "summary": [],
        "skills": [],
        "experience": [],
        "projects": [],
        "education": [],
        "certifications": [],
    }

    current_section = "header"

    for line in resume_text.splitlines():
        detected = _match_section_header(line)
        if detected:
            current_section = detected
            continue
        sections[current_section].append(line)

    # Join each section's lines back into clean text blocks
    return {key: "\n".join(lines).strip() for key, lines in sections.items()}