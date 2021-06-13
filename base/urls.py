from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = "base"

router = DefaultRouter()
# Rutas de usuario
router.register('usuarios', views.ABMUsuarioViewSet, basename="usuario")
router.register('registro', views.RegistroViewSet, basename="registro")

urlpatterns = [
    path('', include(router.urls)),
    path('validar-email/<str:token>', views.validar_token_email, name="activar-cuenta"),
    path('olvido-password/', views.olvido_password, name="olvido-password"),
    path('validar-token/<str:token>', views.validar_token_password, name="validar-token-password"),
    path('cambiar-password/', views.cambiar_password, name="cambiar-password"),
]
