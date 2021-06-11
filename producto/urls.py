from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "backend"

router = DefaultRouter()

# Rutas de productos
router.register('', views.ProductoViewSet)
router.register('abm/', views.ABMProductoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
