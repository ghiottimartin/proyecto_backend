from django.urls import path, include
from rest_framework import routers
from . import views

app_name = "gastronomia"

router = routers.SimpleRouter()
router.register('pedido', views.PedidoEstadoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
