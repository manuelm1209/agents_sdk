from django.urls import path
from . import views

urlpatterns = [
    path("", views.agent_test, name="agent_test"),
]