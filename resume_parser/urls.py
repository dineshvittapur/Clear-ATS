from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("analysis/<int:pk>/", views.analysis_detail, name="analysis_detail"),
    path("analysis/<int:pk>/delete/", views.delete_analysis, name="delete_analysis"),
]