from .skills import extract_skills
from .keyword_parser import extract_keywords

OPTIONAL_CUES = (
    "preferred",
    "nice to have",
    "nice-to-have",
    "bonus",
    "plus",
    "optional",
    "good to have",
    "advantageous",
    "desirable",
)


def parse_job_description(jd_text: str) -> dict:
    """
    Parses a raw job description into structured requirements:
    - required_skills vs. optional_skills
    - top domain keywords (excluding already-tracked skills)
    """
    if not jd_text:
        return {
            "required_skills": [],
            "optional_skills": [],
            "keywords": [],
        }

    required_lines: list[str] = []
    optional_lines: list[str] = []
    in_optional_section = False

    for line in jd_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue

        lower = stripped.lower()

        if len(stripped.split()) <= 6 and any(cue in lower for cue in OPTIONAL_CUES):
            in_optional_section = True
            optional_lines.append(stripped)
            continue

        if (
            len(stripped.split()) <= 6
            and any(word in lower for word in ("required", "requirements", "must have", "responsibilities", "qualifications"))
            and not any(cue in lower for cue in OPTIONAL_CUES)
        ):
            in_optional_section = False
            required_lines.append(stripped)
            continue

        if in_optional_section or any(cue in lower for cue in OPTIONAL_CUES):
            optional_lines.append(stripped)
        else:
            required_lines.append(stripped)

    req_skills = set(extract_skills("\n".join(required_lines)))
    opt_skills = set(extract_skills("\n".join(optional_lines))) - req_skills

    if not req_skills and opt_skills:
        req_skills = opt_skills
        opt_skills = set()

    all_skills = req_skills | opt_skills

    return {
        "required_skills": sorted(req_skills),
        "optional_skills": sorted(opt_skills),
        "keywords": extract_keywords(jd_text, top_n=18, exclude_terms=all_skills),
    }