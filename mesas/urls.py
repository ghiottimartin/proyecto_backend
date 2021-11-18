from django.urls import path, include
from rest_framework import routers
from . import views

app_name = "producto"

router = routers.SimpleRouter()

router.register('mesa', views.MesaViewSet)
router.register('turno', views.TurnoViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
