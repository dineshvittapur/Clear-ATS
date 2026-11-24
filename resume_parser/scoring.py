"""
Auditable, Explainable ATS Scoring Engine.
Implements a transparent weighted linear model tailored for software engineering profiles:
- 60% Core Technical / Domain Skills (with alias-aware project proof multipliers & soft-skill guard)
- 15% Domain Keywords & Concepts
- 15% Practical Project & Experience Evidence
- 10% Education Alignment
"""
import re
from typing import Dict, Any, List, Set, Optional, Iterable
from .skills import get_skill_aliases

CATEGORY_WEIGHTS = {
    "skills": 0.60,
    "keywords": 0.15,
    "experience": 0.15,
    "education": 0.10,
}

PLACEMENT_MULTIPLIERS = {
    "project_verified": 1.00,   # Found in Projects or Experience
    "skills_declared": 0.85,    # Listed in Skills or Certifications summary
    "header_only": 0.50,        # Mentioned only in Header/Objective
}

SOFT_SKILLS = {"Communication", "Teamwork", "Problem Solving", "Critical Thinking"}


def normalize_token_set(items: Optional[Iterable[str]]) -> Set[str]:
    if not items:
        return set()
    return {str(item).strip().lower() for item in items if str(item).strip()}


def extract_years_from_text(text: str) -> Optional[float]:
    if not text:
        return None
    patterns = [
        r"(\d+(?:\.\d+)?)\s*\+?\s*(?:to\s*\d+\s*)?(?:years?|yrs?)(?:\s+of\s+experience)?",
        r"(?:experience\s*:\s*)(\d+(?:\.\d+)?)\s*\+?\s*(?:years?|yrs?)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1))
            except (ValueError, TypeError):
                continue
    return None


def determine_placement(skill: str, resume_sections: Dict[str, str]) -> str:
    """
    Checks where a skill or any of its canonical aliases appeared in the resume.
    Prioritizes Projects/Experience (1.0x) over Skills/Certifications (0.85x).
    """
    aliases = get_skill_aliases(skill)

    project_text = (
        resume_sections.get("projects", "") + " " + resume_sections.get("experience", "")
    ).lower()
    skills_text = (
        resume_sections.get("skills", "") + " " + resume_sections.get("certifications", "")
    ).lower()

    for alias in aliases:
        pat = rf"\b{re.escape(alias)}\b" if len(alias) > 1 else rf"(?<![a-zA-Z0-9_#+]){re.escape(alias)}(?![a-zA-Z0-9_#+])"
        if re.search(pat, project_text):
            return "project_verified"

    for alias in aliases:
        pat = rf"\b{re.escape(alias)}\b" if len(alias) > 1 else rf"(?<![a-zA-Z0-9_#+]){re.escape(alias)}(?![a-zA-Z0-9_#+])"
        if re.search(pat, skills_text):
            return "skills_declared"

    return "skills_declared"


def calculate_tiered_ats_score(
    resume_skills: Optional[List[str]] = None,
    jd_skills: Optional[List[str]] = None,
    resume_keywords: Optional[List[str]] = None,
    jd_keywords: Optional[List[str]] = None,
    resume_sections: Optional[Dict[str, str]] = None,
    jd_text: str = "",
    skill_weights: Optional[Dict[str, float]] = None,
    **kwargs
) -> Dict[str, Any]:
    sections = resume_sections or {}
    weights_dict = skill_weights or {}
    all_jd_skills = jd_skills or []
    res_skills_set = normalize_token_set(resume_skills)

    # -------------------------------------------------------------
    # 1. TECHNICAL / DOMAIN SKILLS SCORE (60% Weight)
    # -------------------------------------------------------------
    total_skill_weight = 0.0
    matched_skill_weight = 0.0
    matched_skills = []
    missing_skills = []
    skill_audit = {}
    hard_skills_required = 0
    hard_skills_matched = 0

    for skill in all_jd_skills:
        base_w = float(weights_dict.get(skill, 1.0))
        total_skill_weight += base_w
        is_soft = skill in SOFT_SKILLS

        if not is_soft:
            hard_skills_required += 1

        if skill.lower() in res_skills_set:
            if not is_soft:
                hard_skills_matched += 1
            matched_skills.append(skill)
            placement = determine_placement(skill, sections)
            multiplier = PLACEMENT_MULTIPLIERS.get(placement, 0.85)
            earned_w = round(base_w * multiplier, 2)
            matched_skill_weight += earned_w
            skill_audit[skill] = {
                "base_weight": base_w,
                "earned_weight": earned_w,
                "placement": placement,
            }
        else:
            missing_skills.append(skill)
            skill_audit[skill] = {
                "base_weight": base_w,
                "earned_weight": 0.0,
                "placement": "missing",
            }

    skills_percentage = (matched_skill_weight / total_skill_weight * 100.0) if total_skill_weight > 0 else 0.0

    # Guard against soft-skill inflation when 0 hard domain skills match
    if hard_skills_required > 0 and hard_skills_matched == 0:
        skills_percentage = min(skills_percentage, 15.0)

    # -------------------------------------------------------------
    # 2. DOMAIN KEYWORDS SCORE (15% Weight)
    # -------------------------------------------------------------
    res_kw_set = normalize_token_set(resume_keywords)
    jd_kw_set = normalize_token_set(jd_keywords)

    matched_kw = set()
    missing_kw = set()

    for kw in jd_kw_set:
        canonical_kw = " ".join(sorted(kw.split()))
        if kw in res_kw_set or canonical_kw in res_kw_set:
            matched_kw.add(kw)
        else:
            missing_kw.add(kw)

    keywords_percentage = (len(matched_kw) / len(jd_kw_set) * 100.0) if jd_kw_set else 100.0

    # -------------------------------------------------------------
    # 3. PRACTICAL EXPERIENCE & PROJECTS (15% Weight)
    # -------------------------------------------------------------
    exp_text = sections.get("experience", "") + " " + sections.get("projects", "")
    jd_req_years = extract_years_from_text(jd_text)
    res_years = extract_years_from_text(exp_text)
    has_projects = bool(sections.get("projects", "").strip())
    has_experience = bool(sections.get("experience", "").strip())

    if jd_req_years is not None and jd_req_years > 0:
        if res_years is not None:
            experience_percentage = min(100.0, (res_years / jd_req_years) * 100.0)
            exp_note = f"Required: {jd_req_years} yrs, Resume shows: {res_years} yrs."
        elif has_projects:
            experience_percentage = 85.0
            exp_note = "Entry-level alignment: Evaluated practical project implementations."
        else:
            experience_percentage = 40.0
            exp_note = f"Role mentions {jd_req_years} yrs experience; limited evidence detected."
    else:
        if has_projects or has_experience:
            experience_percentage = 95.0
            exp_note = "Strong project portfolio detected."
        else:
            experience_percentage = 50.0
            exp_note = "Limited practical project evidence found."

    # -------------------------------------------------------------
    # 4. EDUCATION ALIGNMENT (10% Weight)
    # -------------------------------------------------------------
    edu_text = sections.get("education", "").lower()
    deg_patterns = ["b.tech", "btech", "bachelor", "master", "m.tech", "degree", "computer science", "engineering"]
    found_degrees = [d for d in deg_patterns if d in edu_text]

    if found_degrees:
        education_percentage = 100.0
        edu_note = f"Verified degree credential: {found_degrees[0].upper()}"
    elif edu_text.strip():
        education_percentage = 75.0
        edu_note = "Education section detected."
    else:
        education_percentage = 40.0
        edu_note = "Education credentials not recognized."

    # -------------------------------------------------------------
    # 5. MATHEMATICAL COMPOSITE ATS SCORE
    # -------------------------------------------------------------
    skills_points = skills_percentage * CATEGORY_WEIGHTS["skills"]
    keywords_points = keywords_percentage * CATEGORY_WEIGHTS["keywords"]
    experience_points = experience_percentage * CATEGORY_WEIGHTS["experience"]
    education_points = education_percentage * CATEGORY_WEIGHTS["education"]

    composite_score = skills_points + keywords_points + experience_points + education_points

    return {
        "overall_score": round(composite_score, 2),
        "category_scores": {
            "skills": round(skills_percentage, 2),
            "keywords": round(keywords_percentage, 2),
            "experience": round(experience_percentage, 2),
            "education": round(education_percentage, 2),
        },
        "breakdown": {
            "skills": {
                "score": round(skills_percentage, 1),
                "weight": 60,
                "points": round(skills_points, 1),
            },
            "keywords": {
                "score": round(keywords_percentage, 1),
                "weight": 15,
                "points": round(keywords_points, 1),
            },
            "experience": {
                "score": round(experience_percentage, 1),
                "weight": 15,
                "points": round(experience_points, 1),
            },
            "education": {
                "score": round(education_percentage, 1),
                "weight": 10,
                "points": round(education_points, 1),
            },
        },
        "matched_skill_weight": round(matched_skill_weight, 1),
        "total_skill_weight": round(total_skill_weight, 1),
        "matched_required_skills": sorted(matched_skills),
        "missing_required_skills": sorted(missing_skills),
        "skill_placement_audit": skill_audit,
        "matched_keywords": sorted(list(matched_kw)),
        "missing_keywords": sorted(list(missing_kw)),
        "experience_note": exp_note,
        "education_note": edu_note,
    }