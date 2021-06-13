from backend.token import CustomAuthToken
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('backend.urls', namespace='backend')),
    path('auth/', CustomAuthToken.as_view()),
    path('producto/', include('producto.urls', namespace='producto')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)