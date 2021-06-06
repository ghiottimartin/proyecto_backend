from django.contrib.auth.hashers import make_password
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework import status
from rest_framework.authtoken.views import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import api_view
from .email import enviar_email_registro
from .models import Producto, Usuario
from .serializers import UsuarioSerializer, ProductoSerializer
import secrets
import datetime


# Alta de usuario sin autorización
class RegistroViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def create(self, request, *args, **kwargs):
        serializer = UsuarioSerializer(data=request.data, context={'roles': request.data["roles"]})
        if serializer.is_valid(raise_exception=False):
            serializer.save()
            usuario = buscar_usuario("id", serializer.data["id"])
            usuario.agregar_roles(request.data["roles"])
            usuario.save()
            # email.enviar_email_registro(usuario)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        mensajes = serializer.get_mensaje_errores()
        return Response(mensajes, status=status.HTTP_400_BAD_REQUEST)


# Abm de usuarios con autorización
class ABMUsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]


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
def activar_cuenta(request, token):
    if request.method == "POST":
        try:
            usuario = buscar_usuario("token_email", token)
            if usuario is None:
                return Response(
                    "El token ingresado no es válido o ha caducado. Comuníquese con nosotros mediante la sección.",
                    status=status.HTTP_400_BAD_REQUEST)
            usuario.habilitado = True
            usuario.token_email = None
            usuario.save()
            token = Token.objects.get(user=usuario)
            data = {
                'token': token.key,
                'idUsuario': usuario.pk,
                'nombre': usuario.first_name
            }
            return Response(data, status=status.HTTP_200_OK)
        except:
            return Response("Hubo un error al activar su cuenta. Intente de nuevo más tarde.",
                            status=status.HTTP_400_BAD_REQUEST)
    return Response("Hubo un error al activar su cuenta. Intente de nuevo más tarde.",
                    status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def olvido_password(request):
    error = {"message": "Hubo un error al enviar el email de cambio de contraseña. Intente nuevamente más tarde."}
    if request.method == "POST":
        try:
            stringEmail = request.data["email"]
            usuario = buscar_usuario("email", stringEmail)
            if usuario is None:
                return Response({"message": "El email ingresado no corresponde a ningún usuario registrado."},
                                status=status.HTTP_400_BAD_REQUEST)
            usuario.token_reset = secrets.token_hex(16)
            usuario.fecha_token_reset = datetime.datetime.today()
            usuario.save()
            enviar_email_registro(usuario)
            exito = {"message": "Se ha enviado un link a su email para reiniciar su contraseña. Tiene 24 horas para "
                                "cambiarla."}
            return Response(exito, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
    return Response(error, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def validar_token_password(request, token):
    error = {"message": "Hubo un error intentar validar el link. Intente de nuevo más tarde."}
    if request.method == "POST":
        try:
            usuario = buscar_usuario_token_reset(token)
            if usuario is None:
                return Response({"message": "El link ingresado no es válido o ha caducado. Vuelva a solicitar el "
                                            "cambio de contraseña."}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"message": "Ahora puede cambiar su contraseña."}, status=status.HTTP_200_OK)
        except:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
    return Response(error, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def cambiar_password(request):
    error = {"message": "Hubo un error cambiar la contraseña. Intente de nuevo más tarde."}
    if request.method == "POST":
        try:
            token = request.data["token"]
            usuario = buscar_usuario_token_reset(token)
            if usuario is None:
                return Response(error, status=status.HTTP_400_BAD_REQUEST)
            password = request.data["password"]
            usuario.password = make_password(password)
            usuario.fecha_token_reset = None
            usuario.save()
            return Response({"message": "La contraseña fue cambiada con éxito, intente ingresar nuevamente."},
                            status=status.HTTP_200_OK)
        except:
            return Response(error, status=status.HTTP_400_BAD_REQUEST)
    return Response(error, status=status.HTTP_400_BAD_REQUEST)


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
