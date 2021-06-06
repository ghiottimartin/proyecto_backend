from django.contrib.auth.hashers import make_password
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.authtoken.views import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Producto, Usuario
from .serializers import UsuarioSerializer, ProductoSerializer
from . import email
from . import respuestas
import datetime
import secrets


# Alta de usuario sin autorización
class RegistroViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def create(self, request, *args, **kwargs):
        return crear_usuario(True, request)


# Abm de usuarios con autorización
class ABMUsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        return crear_usuario(False, request)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        password = request.data["password"]
        if request.data["password"] == "":
            password = instance.password
        else:
            password = make_password(password)
        request.data["password"] = password
        if request.data["dni"] == "":
            request.data["dni"] = None
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'roles': request.data["roles"]}
                                         )
        valid = serializer.is_valid(raise_exception=False)
        if valid:
            self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        errores = serializer.get_errores_lista()
        if len(errores) > 0:
            return respuestas.get_respuesta(False, errores)
        return respuestas.get_respuesta(True, "El usuario se ha actualizado con éxito.", None, {"usuario": serializer.data})


def crear_usuario(enviar, request):
    serializer = UsuarioSerializer(data=request.data, context={'roles': request.data["roles"]})
    if serializer.is_valid(raise_exception=False):
        serializer.save()
        usuario = buscar_usuario("id", serializer.data["id"])
        usuario.agregar_roles(request.data["roles"])
        usuario.save()
        if enviar:
            pass
        #   email.enviar_email_registro(usuario)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    errores = serializer.get_errores_lista()
    return respuestas.get_respuesta(False, errores)


# Obtención de productos sin autorización
class ProductoViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


# Abm de productos con autorización
class ABMProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
def validar_token_email(request, token):
    if request.method == "POST":
        try:
            usuario = buscar_usuario("token_email", token)
            if usuario is None:
                return respuestas.validar_token_email_error_token_invalido()
            usuario.habilitado = True
            usuario.token_email = None
            usuario.save()
            token = Token.objects.get(user=usuario)
            data = {
                'token': token.key,
                'idUsuario': usuario.pk,
                'nombre': usuario.first_name
            }
            return respuestas.get_respuesta(exito=True, mensaje="", codigo=None, datos=data)
        except:
            return respuestas.validar_token_email_error_general()
    return respuestas.validar_token_email_error_general()


@api_view(['POST'])
def olvido_password(request):
    if request.method == "POST":
        try:
            stringEmail = request.data["email"]
            usuario = buscar_usuario("email", stringEmail)
            if usuario is None:
                return respuestas.olvido_password_error_email_inexistente()
            usuario.token_reset = secrets.token_hex(16)
            usuario.fecha_token_reset = datetime.datetime.today()
            usuario.save()
            email.enviar_email_cambio_password(usuario)
            return respuestas.olvido_password_exito()
        except:
            return respuestas.olvido_password_error_general()
    return respuestas.olvido_password_error_general()


@api_view(['POST'])
def validar_token_password(request, token):
    if request.method == "POST":
        try:
            usuario = buscar_usuario_token_reset(token)
            if usuario is None:
                return respuestas.validar_token_password_error_link_invalido()
            return respuestas.exito()
        except:
            return respuestas.validar_token_password_error_general()
    return respuestas.validar_token_password_error_general()


@api_view(['POST'])
def cambiar_password(request):
    if request.method == "POST":
        try:
            token = request.data["token"]
            usuario = buscar_usuario_token_reset(token)
            if usuario is None:
                return respuestas.cambiar_password_error_general()
            password = request.data["password"]
            usuario.password = make_password(password)
            usuario.token_reset = None
            usuario.fecha_token_reset = None
            usuario.save()
            return respuestas.cambiar_password_exito()
        except:
            return respuestas.cambiar_password_error_general()
    return respuestas.cambiar_password_error_general()


# Búsqueda genérica de usuario por un campo
def buscar_usuario(campo, valor):
    filtro = {campo: valor}
    try:
        return Usuario.objects.get(**filtro)
    except Usuario.DoesNotExist:
        return None


# Busca un usuario que tenga el token reset enviado como parámetro y si el usuario posee fecha_token_reset la
# diferencia con la fecha actual debe ser menor o igual a un día
def buscar_usuario_token_reset(token):
    try:
        usuario = Usuario.objects.get(token_reset=token)
        if usuario is not None and usuario.fecha_token_reset is None:
            return usuario
        naive = usuario.fecha_token_reset.replace(tzinfo=None)
        delta = datetime.datetime.today() - naive
        if delta.days > 1:
            return None
        return usuario
    except Usuario.DoesNotExist:
        return None
    except Exception as ex:
        return None
