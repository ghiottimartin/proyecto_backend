from django.urls import path

from . import views

app_name = "backend"

urlpatterns = [
    path("productos/", views.listar_productos, name="productos"),
]
