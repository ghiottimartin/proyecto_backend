from django.urls import path, include
from rest_framework import routers
from . import views

app_name = "producto"

router = routers.SimpleRouter()

# Rutas de productos
router.register('', views.ProductoViewSet)
router.register('abm/', views.ABMProductoViewSet)
router.register('categorias/', views.CategoriaViewSet)
router.register('abm/categorias/', views.ABMCategoriaViewSet)
router.register('ingreso/', views.ABMIngresoViewSet)
router.register('movimientos/', views.MovimientoStockViewSet)
router.register('reemplazos/', views.ReemplazoMercaderiViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
