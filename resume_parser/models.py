from django.db import models


class ResumeAnalysis(models.Model):
    # 1. Raw Inputs
    job_title = models.CharField(max_length=200, blank=True, default="Target Role")
    resume_file = models.FileField(upload_to="resumes/")
    resume_text = models.TextField(blank=True)
    job_description = models.TextField()

    # 2. Parsed Structured Data (stored as JSON for transparency)
    parsed_sections = models.JSONField(default=dict, blank=True)
    matched_required_skills = models.JSONField(default=list, blank=True)
    missing_required_skills = models.JSONField(default=list, blank=True)
    matched_optional_skills = models.JSONField(default=list, blank=True)
    missing_optional_skills = models.JSONField(default=list, blank=True)
    skill_placement_audit = models.JSONField(default=dict, blank=True)
    matched_keywords = models.JSONField(default=list, blank=True)
    missing_keywords = models.JSONField(default=list, blank=True)
    experience_details = models.JSONField(default=dict, blank=True)
    education_details = models.JSONField(default=dict, blank=True)

    # 3. Explainable ATS Score Breakdown (0 to 100 scale)
    overall_score = models.FloatField(default=0.0)
    required_skills_score = models.FloatField(default=0.0)
    optional_skills_score = models.FloatField(default=0.0)
    keywords_score = models.FloatField(default=0.0)
    experience_score = models.FloatField(default=0.0)
    education_score = models.FloatField(default=0.0)

    # 4. Rule-based Recommendations & Metadata
    recommendations = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Resume Analyses"

    def __str__(self):
        return f"{self.job_title} — {self.overall_score:.1f}% ({self.created_at:%Y-%m-%d})"