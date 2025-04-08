from django.contrib import admin
from django.urls import path, include
from sf_connection_test.views import test_salesforce_connection

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('sf_connection_test.urls')),
    path('agents/', include('agents_test.urls')),
    path('notion/', include('notion_dashboard.urls')),
]
