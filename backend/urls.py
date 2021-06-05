from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "backend"

router = DefaultRouter()
router.register('productos', views.ProductoViewSet, basename="productos")
router.register('abm/producto', views.ABMProductoViewSet, basename="abm-producto")

urlpatterns = [
    path('', include(router.urls)),
    path('registro/', views.registro, name="registro"),
    path('usuarios/', views.UsuarioApiView.as_view(), name="usuarios"),
    path('usuarios/<int:id>', views.UsuarioApiView.as_view(), name="usuarios"),
    
]
