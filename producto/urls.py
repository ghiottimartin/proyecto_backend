from django.urls import path, include
from rest_framework import routers
from . import views

app_name = "producto"

router = routers.SimpleRouter()

# Rutas de productos
router.register('', views.ProductoViewSet)
router.register('abm/', views.ABMProductoViewSet)
router.register('categorias/', views.CategoriaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]