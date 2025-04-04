from django.urls import path
from . import views

urlpatterns = [
    path("", views.notion_dashboard, name="notion_dashboard"),
]