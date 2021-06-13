from django.contrib.auth.hashers import make_password
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.authtoken.views import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .models import Usuario, Rol
from .serializers import UsuarioSerializer
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
        esAdmin = request.user.esAdmin
        instance = self.get_object()
        password = request.data["password"]
        if request.data["password"] == "":
            password = instance.password
        else:
            password = make_password(password)
        request.data["password"] = password
        if request.data["dni"] == "":
            request.data["dni"] = None
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance, data=request.data, partial=partial, context={'roles': request.data["roles"]})
        valid = serializer.is_valid(raise_exception=False)
        tipoRuta = request.data["tipoRuta"]
        if tipoRuta == 'admin' and esAdmin is not True:
            return respuestas.get_respuesta(False, "No está autorizado para realizar esta operación.", None)
        if tipoRuta == 'admin' and esAdmin:
            instance.actualizar_roles(request.data)
        if valid:
            serializer.save()

        errores = serializer.get_errores_lista()
        if len(errores) > 0:
            return respuestas.get_respuesta(False, errores)
        return respuestas.get_respuesta(True, "El usuario se ha actualizado con éxito.", None, {"usuario": serializer.data, "esAdmin": esAdmin})

    def list(self, request, *args, **kwargs):
        usuarios = Usuario.objects.all().exclude(roles__in=Rol.objects.filter(nombre=Rol.ADMINISTRADOR))
        serializer = UsuarioSerializer(instance=usuarios, many=True)
        return respuestas.get_respuesta(True, "", None, {"usuarios": serializer.data})


def crear_usuario(enviar, request):
    roles = get_roles_usuario(request.data)
    serializer = UsuarioSerializer(data=request.data, context={'roles': roles})
    if serializer.is_valid(raise_exception=False):
        serializer.save()
        usuario = buscar_usuario("id", serializer.data["id"])
        if request.data['tipoRegistro'] == 'admin':
            usuario.password = make_password(str(usuario.dni))
        usuario.agregar_roles(roles)
        usuario.save()
        if enviar:
            pass
        #   email.enviar_email_registro(usuario)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    errores = serializer.get_errores_lista()
    return respuestas.get_respuesta(False, errores)


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
            #email.enviar_email_cambio_password(usuario)
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


def get_roles_usuario(usuario):
    roles = []
    if 'esMozo' in usuario and usuario.get('esMozo'):
        roles.append(Rol.MOZO)
    if 'esComensal' in usuario and usuario.get('esComensal'):
        roles.append(Rol.COMENSAL)
    if 'esVendedor' in usuario and usuario.get('esVendedor'):
        roles.append(Rol.VENEDEDOR)
    return roles