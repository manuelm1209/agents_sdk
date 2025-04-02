from django.urls import path
from . import views

urlpatterns = [
    path("", views.test_salesforce_connection, name="sf_connection_test"),
    path("affiliations/", views.query_salesforce_affiliations, name="sf_affiliation_query"),
]