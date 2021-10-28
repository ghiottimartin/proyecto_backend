from django.urls import path, include
from rest_framework import routers
from . import views

app_name = "gastronomia"

router = routers.SimpleRouter()
router.register('pedido', views.PedidoViewSet)
router.register('venta/', views.ABMVentaViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
