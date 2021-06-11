from backend.token import CustomAuthToken
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.urls', namespace='backend')),
    path('auth/', CustomAuthToken.as_view()),
    path('producto/', include('producto.urls', namespace='producto')),
]
