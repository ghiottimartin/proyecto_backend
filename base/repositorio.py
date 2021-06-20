from base import email
from base.models import Usuario, Rol
from base.respuestas import Respuesta
from base.serializers import UsuarioSerializer
from django.contrib.auth.hashers import make_password
import datetime
from django.db import transaction

respuesta = Respuesta()


# Busca el rol por nombre.
def get_rol(rol):
    try:
        return Rol.objects.get(nombre=rol)
    except Rol.DoesNotExist:
        return None


@transaction.atomic
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
