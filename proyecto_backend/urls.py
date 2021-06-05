from backend.token import CustomAuthToken
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.urls')),
    path('auth/', CustomAuthToken.as_view())
]
