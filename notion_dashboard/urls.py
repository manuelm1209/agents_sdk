from django.urls import path
from . import views

urlpatterns = [
    path('', views.notion_dashboard, name='notion_dashboard'),
    path('fetch-data/', views.fetch_notion_data, name='fetch_notion_data'),
]