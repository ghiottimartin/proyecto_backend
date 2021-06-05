from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "backend"

router = DefaultRouter()
router.register('usuarios', views.UsuarioViewSet, basename="usuarios")
router.register('productos', views.ProductoViewSet, basename="productos")

urlpatterns = [
    path('', include(router.urls)),
]
