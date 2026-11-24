from typing import Dict, Any, List


def generate_recommendations(score_result: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Generates explainable, prioritized recommendations directly from
    calculate_tiered_ats_score() audit results.
    """
    recs: List[Dict[str, str]] = []

    missing_skills = score_result.get("missing_required_skills", [])
    audit = score_result.get("skill_placement_audit", {})
    missing_kw = score_result.get("missing_keywords", [])
    breakdown = score_result.get("breakdown", {})

    # 1. High-Priority: Missing Core JD Skills
    if missing_skills:
        top_missing = ", ".join(missing_skills[:6])
        recs.append({
            "priority": "High",
            "category": "Missing Core Skills",
            "title": f"Add or build evidence for {len(missing_skills)} missing skill(s)",
            "detail": f"Your resume does not mention: {top_missing}. Consider building a mini-project or adding relevant coursework/experience demonstrating these skills.",
        })

    # 2. Medium-Priority: Skills listed only in Skills section (0.85x multiplier vs 1.0x)
    declared_only = [
        skill for skill, info in audit.items()
        if info.get("placement") == "skills_declared"
    ]
    if declared_only:
        sample = ", ".join(declared_only[:5])
        recs.append({
            "priority": "Medium",
            "category": "Project Verification Multiplier",
            "title": "Prove declared skills inside Projects or Experience (0.85x -> 1.00x)",
            "detail": f"Skills like {sample} appear only in your Skills list. Mentioning how you used them in Projects or Experience boosts their weight from 85% to 100%.",
        })

    # 3. Medium-Priority: Missing Domain Keywords
    if len(missing_kw) >= 3:
        sample_kw = ", ".join(missing_kw[:6])
        recs.append({
            "priority": "Medium",
            "category": "Domain Keywords",
            "title": "Weave missing domain concepts into bullet points",
            "detail": f"Incorporate natural references to key terms from the job description such as: {sample_kw}.",
        })

    # 4. Experience / Project Evidence
    exp_score = breakdown.get("experience", {}).get("score", 100)
    if exp_score < 85:
        recs.append({
            "priority": "Medium",
            "category": "Experience & Projects",
            "title": "Strengthen practical project or tenure evidence",
            "detail": score_result.get("experience_note", "Add quantified project outcomes and clear date ranges."),
        })

    # 5. Education Alignment
    edu_score = breakdown.get("education", {}).get("score", 100)
    if edu_score < 100:
        recs.append({
            "priority": "Low",
            "category": "Education",
            "title": "Clarify degree credentials",
            "detail": score_result.get("education_note", "Explicitly list your full degree title (e.g., B.Tech in Computer Science)."),
        })

    if not recs:
        recs.append({
            "priority": "Info",
            "category": "Strong Match",
            "title": "Your resume aligns strongly with this job description",
            "detail": "All core skills are project-verified. Focus on quantifying impact metrics in your bullet points.",
        })

    return recs