from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "backend"

router = DefaultRouter()
router.register('usuarios', views.ABMUsuarioViewSet, basename="usuario")
router.register('productos', views.ProductoViewSet, basename="productos")
router.register('abm/producto', views.ABMProductoViewSet, basename="abm-producto")

urlpatterns = [
    path('', include(router.urls)),
    path('registro/', views.registro, name="registro"),
    
]
