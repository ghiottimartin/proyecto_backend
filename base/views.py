from django.contrib.auth.hashers import make_password
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.authtoken.views import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from .models import Usuario, Rol
from .serializers import UsuarioSerializer
from . import email
from base.respuestas import Respuesta
import datetime
import secrets

respuesta = Respuesta()


# Alta de usuario sin autorización
class RegistroViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Usuario.objects.filter(borrado=False)
    serializer_class = UsuarioSerializer

    def create(self, request, *args, **kwargs):
        return crear_usuario(True, request)


# Abm de usuarios con autorización
class ABMUsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.filter(borrado=False)
    serializer_class = UsuarioSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        return crear_usuario(False, request)

    def update(self, request, *args, **kwargs):
        # Verifico que tenga permiso para actualizar usuarios.
        esAdmin = request.user.esAdmin
        tipoRuta = request.data["tipoRuta"] if "tipoRuta" in request.data else "comun"
        if tipoRuta == 'admin' and not esAdmin:
            return respuesta.get_respuesta(False, "No está autorizado para realizar esta operación.", None)

        # Actualizo datos del usuario.
        usuario = self.get_object()
        actualizada = self.actualizar_campos_request(request, usuario)
        serializer = UsuarioSerializer(data=actualizada.data, instance=usuario)
        valido = serializer.is_valid(raise_exception=False)
        if not valido:
            errores = serializer.get_errores_lista()
            return respuesta.get_respuesta(False, errores)

        # Guardo cambios del usuario.
        serializer.save()
        if tipoRuta == 'admin' and esAdmin:
            usuario.actualizar_roles(actualizada.data)
            usuario.save()
        return respuesta.get_respuesta(True, "El usuario se ha actualizado con éxito.", None,
                                       {"usuario": serializer.data, "esAdmin": esAdmin})

    def list(self, request, *args, **kwargs):
        usuarios = Usuario.objects.filter(borrado=False).exclude(roles__in=Rol.objects.filter(nombre=Rol.ADMINISTRADOR))
        serializer = UsuarioSerializer(instance=usuarios, many=True)
        return respuesta.get_respuesta(True, "", None, {"usuarios": serializer.data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        puede_borrarse = instance.comprobar_puede_borrarse()
        if puede_borrarse:
            return respuesta.get_respuesta(False, "El usuario no puede ser borrado debido a que se encuentra "
                                                  "relacionado a los datos de la web.")
        instance.borrado = True
        instance.save()
        return respuesta.get_respuesta(True, "El usuario se ha borrado con éxito")

    # Actualiza la contraseña del usuario según la request. Si la cambió se actualiza sino devuelve la actual.
    def actualizar_password(self, usuario, request):
        password = request.data["password"]
        if request.data["password"] == "":
            password = usuario.password
        else:
            password = make_password(password)
        return password

    # Actualiza la contraseña y inicializa campos vacíos.
    def actualizar_campos_request(self, request, usuario):
        request.data["password"] = self.actualizar_password(usuario, request)
        if request.data["dni"] == "":
            request.data["dni"] = None
        return request


def crear_usuario(enviar, request):
    # Verifico que los datos sean válidos.
    serializer = UsuarioSerializer(data=request.data)
    if not serializer.is_valid(raise_exception=False):
        errores = serializer.get_errores_lista()
        return respuesta.get_respuesta(False, errores)

    # Guardo campos genéricos del usuario.
    serializer.save()

    # Si lo está creando un usuario administrador le pongo como contraseña el dni y agrego los roles según los campos
    # booleanos. Sino le agrego el rol comensal.
    usuario = buscar_usuario("id", serializer.data["id"])
    tipoAdmin = request.data['tipoRegistro'] == 'admin'
    if tipoAdmin:
        usuario.password = make_password(str(usuario.dni))
        usuario.actualizar_roles(request.data)
    else:
        usuario.agregar_rol_comensal()
    usuario.save()
    if enviar:
        pass
    #   email.enviar_email_registro(usuario)
    return respuesta.exito()


# Comprueba que el link del email para habilitar el usuario sea válido.
@api_view(['POST'])
def validar_token_email(request, token):
    if request.method == "POST":
        try:
            usuario = buscar_usuario("token_email", token)
            if usuario is None:
                return respuesta.validar_token_email_error_token_invalido()
            usuario.habilitado = True
            usuario.token_email = None
            usuario.save()
            token = Token.objects.get(user=usuario)
            data = {
                'token': token.key,
                'idUsuario': usuario.pk,
                'nombre': usuario.first_name
            }
            return respuesta.get_respuesta(exito=True, mensaje="", codigo=None, datos=data)
        except:
            return respuesta.validar_token_email_error_general()
    return respuesta.validar_token_email_error_general()


# Envía un email al usuario para que cambie su contraseña.
@api_view(['POST'])
def olvido_password(request):
    if request.method == "POST":
        try:
            stringEmail = request.data["email"]
            usuario = buscar_usuario("email", stringEmail)
            if usuario is None:
                return respuesta.olvido_password_error_email_inexistente()
            usuario.token_reset = secrets.token_hex(16)
            usuario.fecha_token_reset = datetime.datetime.today()
            usuario.save()
            # email.enviar_email_cambio_password(usuario)
            return respuesta.olvido_password_exito()
        except:
            return respuesta.olvido_password_error_general()
    return respuesta.olvido_password_error_general()


# Comprueba que el link del email para cambiar la contraseña sea válido.
@api_view(['POST'])
def validar_token_password(request, token):
    if request.method == "POST":
        try:
            usuario = buscar_usuario_token_reset(token)
            if usuario is None:
                return respuesta.validar_token_password_error_link_invalido()
            return respuesta.exito()
        except:
            return respuesta.validar_token_password_error_general()
    return respuesta.validar_token_password_error_general()


# Cambia la contraseña del usuario.
@api_view(['POST'])
def cambiar_password(request):
    if request.method == "POST":
        try:
            token = request.data["token"]
            usuario = buscar_usuario_token_reset(token)
            if usuario is None:
                return respuesta.cambiar_password_error_general()
            password = request.data["password"]
            usuario.password = make_password(password)
            usuario.token_reset = None
            usuario.fecha_token_reset = None
            usuario.save()
            return respuesta.cambiar_password_exito()
        except Exception as ex:
            return respuesta.cambiar_password_error_general()
    return respuesta.cambiar_password_error_general()


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
