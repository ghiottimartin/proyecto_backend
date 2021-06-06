from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "backend"

router = DefaultRouter()
#Rutas de usuario
router.register('usuarios', views.ABMUsuarioViewSet, basename="usuario")
router.register('registro', views.RegistroViewSet, basename="registro")

#Rutas de productos
router.register('productos', views.ProductoViewSet, basename="productos")
router.register('abm/producto', views.ABMProductoViewSet, basename="abm-producto")

urlpatterns = [
    path('', include(router.urls)),
    path('validar-email/<str:token>', views.activar_cuenta, name="activar-cuenta"),
    path('olvido-password/', views.olvido_password, name="olvido-password"),
    path('validar-token/<str:token>', views.validar_token_password, name="validar-token-password"),
    path('cambiar-password/', views.cambiar_password, name="cambiar-password"),
]
