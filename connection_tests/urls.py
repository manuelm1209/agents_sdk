from django.urls import path
from . import views

urlpatterns = [
    # Salesforce connection routes
    path("", views.test_salesforce_connection, name="sf_connection_test"),
    path("affiliations/", views.query_salesforce_affiliations, name="sf_affiliation_query"),
    
    # DashWorks routes
    path("chat/", views.dashworks_chat, name="dashworks_chat"),
    path("api-test/", views.test_dashworks_api, name="dashworks_api_test"),
    path("debug/", views.debug_info, name="debug_info"),
    path("curl-test/", views.curl_test, name="curl_test"),
    
    # Notion Dashboard routes
    path("notion/", views.notion_dashboard, name="notion_dashboard"),
    path("notion/fetch-data/", views.fetch_notion_data, name="fetch_notion_data"),
]