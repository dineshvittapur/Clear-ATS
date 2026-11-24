from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import ResumeAnalysis


@admin.register(ResumeAnalysis)
class ResumeAnalysisAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "job_title",
        "overall_score",
        "required_skills_score",
        "keywords_score",
        "experience_score",
        "education_score",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("job_title", "resume_text", "job_description")
    readonly_fields = ("created_at",)