from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.db import transaction
from django.http import FileResponse
from django.views.static import serve
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.authtoken.views import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from .models import Usuario, Rol
from .serializers import UsuarioSerializer
from . import email
from base.respuestas import Respuesta
import datetime
import secrets
import os

respuesta = Respuesta()


# Alta de usuario sin autorización
class RegistroViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Usuario.objects.filter(borrado=False)
    serializer_class = UsuarioSerializer

    @transaction.atomic
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

        # Si puede ser habilitado lo habilitado.
        usuario = self.get_object()
        habilitado = request.query_params.get('habilitado', False)
        if habilitado == 'true':
            usuario.habilitado = True
            usuario.observaciones = ""
            usuario.save()
            return respuesta.get_respuesta(True, "Usuario habilitado con éxito")

        # Actualizo datos del usuario.
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

    # Devuelve los filtros de la query.
    def get_filtros(self, request):
        filtros = {}

        # Agrega filtros por nombre de usuario
        nombre = request.query_params.get('nombre', None)
        if nombre != "":
            filtros["first_name__icontains"] = nombre

        # Agrega filtros por dni
        dni = request.query_params.get('dni', None)
        if dni is not None and dni.isnumeric() and int(dni) > 0:
            filtros["dni__icontains"] = dni

        # Agrega filtros por rol
        rol = request.query_params.get('rol', None)
        if rol != '':
            filtros["roles__nombre__contains"] = rol

        # Agrega filtro por estado
        estado = request.query_params.get('estado', "")
        if estado != "":
            filtros["habilitado"] = True if estado == "activo" else False

        # Agrega filtros por número de página actual
        pagina = int(request.query_params.get('paginaActual', 1))
        registros = int(request.query_params.get('registrosPorPagina', 10))
        offset = (pagina - 1) * registros
        limit = offset + registros
        filtros["offset"] = offset
        filtros["limit"] = limit
        return filtros

        # Devuelve los cantidad de registros sin tener en cuenta la página actual.

    def get_cantidad_registros(self, request):
        filtros = self.get_filtros(request)
        id = filtros.get("id")
        if id is None:
            filtros.pop("offset")
            filtros.pop("limit")
        cantidad = Usuario.objects.filter(**filtros).exclude(roles__nombre__contains=Rol.ADMINISTRADOR).count()
        return cantidad

    # Devuelve los usuarios según los filtros de la query
    def filtrar_usuarios(self, request):
        filtros = self.get_filtros(request)
        offset = filtros.get("offset")
        limit = filtros.get("limit")
        filtros.pop("offset")
        filtros.pop("limit")
        usuarios = Usuario.objects.filter(**filtros).exclude(roles__nombre__contains=Rol.ADMINISTRADOR).order_by('-auditoria_creado_fecha')[offset:limit]
        return usuarios

    # Lista los usuarios aplicando los filtros.
    def list(self, request, *args, **kwargs):
        usuarios = self.filtrar_usuarios(request)
        if len(usuarios) > 0:
            serializer = UsuarioSerializer(instance=usuarios, many=True)
            usuarios = serializer.data

        cantidad = self.get_cantidad_registros(request)
        total = Usuario.objects.exclude(roles__nombre__contains=Rol.ADMINISTRADOR).count()
        datos = {
            "total": total,
            "usuarios": usuarios,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        motivo = request.query_params.get('motivo', "")
        if isinstance(motivo, str) and len(motivo) > 0:
            instance.habilitado = False
            instance.observaciones = motivo
            instance.save()
            email.enviar_email_usuario_deshabilitado(instance)
            return respuesta.get_respuesta(True, "El usuario ha sido inhabilitado con exito")

        puede_borrarse = instance.comprobar_puede_borrarse()
        if not puede_borrarse:
            return respuesta.get_respuesta(False, "El usuario no puede ser borrado debido a que se encuentra "
                                                  "relacionado a los datos de la web.")
        instance.borrado = True
        instance.save()
        email.enviar_email_usuario_deshabilitado(instance)
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

    @action(detail=False, methods=['get'])
    def mozos(self, request, pk=None):
        try:
            objetos = Usuario.objects.filter(roles__nombre__contains=Rol.MOZO).exclude(roles__nombre__contains=Rol.ADMINISTRADOR)
            serializer = UsuarioSerializer(instance=objetos, many=True)
            mozos = serializer.data
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Hubo un error al buscar los mozos.")
        return respuesta.get_respuesta(exito=True, datos={"mozos": mozos})

    @action(detail=True, methods=['get'])
    def manual(self, request, pk=0):
        try:
            filename = "manual-usuario-v1.0.pdf"
            filepath = os.path.join(settings.MEDIA_ROOT, filename)
            return FileResponse(open(filepath, 'rb'), content_type='application/pdf')
        except FileNotFoundError:
            return respuesta.get_respuesta(exito=False, mensaje="Hubo un error al descargar el pdf.")



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
        email.enviar_email_registro(usuario)
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
            email.enviar_email_cambio_password(usuario)
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
        if usuario is not None:
            naive = usuario.fecha_token_reset.replace(tzinfo=None)
            delta = datetime.datetime.today() - naive
            if delta.days > 1:
                return None
            return usuario
    except:
        return None
