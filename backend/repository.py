from rest_framework import status
from rest_framework.authtoken.views import Token
from rest_framework.response import Response
from .models import Usuario, Rol

def get_rol(rol):
    if rol is None:
        rol = Rol.COMENSAL
    try:
        return Rol.objects.get(nombre=Rol.COMENSAL)
    except Rol.DoesNotExist:
        return None

def crear_usuario(first_name, username, password, email, rol):
        try:
            rol = get_rol(rol)
            if rol == None:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            usuario = Usuario.objects.create(first_name=first_name, username=username, password=password, email=email)
            usuario.add_rol(rol)
            Token.objects.create(user=usuario)
            usuario.save()
            return Response(status=status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({"Error": str(ex)}, status=status.HTTP_400_BAD_REQUEST)


    