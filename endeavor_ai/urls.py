from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('', include('core.urls')),  # Use the core app for home
    path('admin/', admin.site.urls),
    path('connections/', include('connection_tests.urls')),
]
