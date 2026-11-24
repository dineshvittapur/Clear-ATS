from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import ResumeAnalysis
from .parser import extract_text_from_pdf
from .resume_sections import parse_resume_sections
from .skills import extract_skills
from .keyword_parser import extract_keywords
from .job_parser import parse_job_description
from .scoring import calculate_tiered_ats_score
from .recommendations import generate_recommendations


def index(request):
    if request.method == "POST":
        job_description = request.POST.get("job_description", "").strip()
        first_line = job_description.splitlines()[0].strip("#* -:")[:80] if job_description else "Target Role"
        job_title = request.POST.get("job_title", "").strip() or first_line or "Target Role"
        resume_file = request.FILES.get("resume_file")

        if not resume_file or not job_description:
            messages.error(request, "Please upload a PDF resume and paste a job description.")
            return redirect("index")

        if not resume_file.name.lower().endswith(".pdf"):
            messages.error(request, "Only PDF files are supported.")
            return redirect("index")

        resume_text = extract_text_from_pdf(resume_file)
        if not resume_text:
            messages.error(request, "Could not extract text from this PDF. Ensure it is not a scanned image.")
            return redirect("index")

        parsed_sections = parse_resume_sections(resume_text)
        resume_skills = extract_skills(resume_text)
        resume_keywords = extract_keywords(resume_text, top_n=None)

        jd_data = parse_job_description(job_description)
        all_jd_skills = jd_data["required_skills"] + jd_data["optional_skills"]

        skill_lower_set = {s.lower() for s in all_jd_skills}
        filtered_jd_keywords = [
            kw for kw in jd_data["keywords"]
            if kw.lower() not in skill_lower_set
        ]

        skill_weights = {s: 1.0 for s in jd_data["required_skills"]}
        skill_weights.update({s: 0.5 for s in jd_data["optional_skills"]})

        score_result = calculate_tiered_ats_score(
            resume_skills=resume_skills,
            jd_skills=all_jd_skills,
            resume_keywords=resume_keywords,
            jd_keywords=filtered_jd_keywords,
            resume_sections=parsed_sections,
            jd_text=job_description,
            skill_weights=skill_weights,
        )

        recs = generate_recommendations(score_result)

        req_set = set(jd_data["required_skills"])
        opt_set = set(jd_data["optional_skills"])
        matched_all = set(score_result["matched_required_skills"])
        missing_all = set(score_result["missing_required_skills"])

        analysis = ResumeAnalysis.objects.create(
            job_title=job_title,
            resume_file=resume_file,
            resume_text=resume_text,
            job_description=job_description,
            parsed_sections=parsed_sections,
            matched_required_skills=sorted(matched_all & req_set),
            missing_required_skills=sorted(missing_all & req_set),
            matched_optional_skills=sorted(matched_all & opt_set),
            missing_optional_skills=sorted(missing_all & opt_set),
            skill_placement_audit=score_result["skill_placement_audit"],
            matched_keywords=score_result["matched_keywords"],
            missing_keywords=score_result["missing_keywords"],
            experience_details={"note": score_result["experience_note"]},
            education_details={"note": score_result["education_note"]},
            overall_score=score_result["overall_score"],
            required_skills_score=score_result["category_scores"]["skills"],
            keywords_score=score_result["category_scores"]["keywords"],
            experience_score=score_result["category_scores"]["experience"],
            education_score=score_result["category_scores"]["education"],
            recommendations=recs,
        )

        return redirect("analysis_detail", pk=analysis.pk)

    recent_analyses = ResumeAnalysis.objects.all()[:10]
    return render(request, "resume_parser/index.html", {"recent_analyses": recent_analyses})


def analysis_detail(request, pk):
    analysis = get_object_or_404(ResumeAnalysis, pk=pk)
    return render(request, "resume_parser/detail.html", {"analysis": analysis})


def delete_analysis(request, pk):
    analysis = get_object_or_404(ResumeAnalysis, pk=pk)
    if request.method == "POST":
        analysis.delete()
        messages.success(request, "Analysis record deleted.")
    return redirect("index")