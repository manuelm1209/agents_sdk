from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('core.urls')),  # Use the core app for home
    path('admin/', admin.site.urls),
    path('sf_connection/', include('sf_connection_test.urls')),
    path('agents/', include('agents_test.urls')),
    path('notion/', include('notion_dashboard.urls')),
]
