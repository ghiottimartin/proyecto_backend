from rest_framework import serializers
from rest_framework.authtoken.views import Token
from rest_framework.exceptions import ValidationError
from .models import Usuario, Rol
import secrets


# ModelSerializer que permite devolver los mensajes en forma de lista de cadenas de texto.
class CustomModelSerializer(serializers.ModelSerializer):

    def get_errores_lista(self, errores=None):
        mensajes = []
        if errores is None:
            errores = self.errors
        for key in errores:
            error = errores[key][0]
            if isinstance(error, str):
                texto = key.capitalize() + ": " + error.capitalize()
                mensajes.append(texto)
            elif isinstance(error, dict):
                recursivos = self.get_errores_lista(error)
                mensajes = mensajes + recursivos
        return mensajes


# Serializador de los roles del usuario.
class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'


# Serializador del usuario.
class UsuarioSerializer(CustomModelSerializer):
    roles = RolSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'roles', 'habilitado', 'password', 'dni', 'operaciones',
                  'esAdmin', 'esMozo', 'esComensal', 'esVendedor']

    # Verifica que los datos recibidos del usuario sean válidos, validando los roles del usuario.
    def is_valid(self, raise_exception=False):
        roles = self.context["roles"]
        if isinstance(roles, list):
            roles = self.convertir_lista_roles(roles)
        invalidos = comprobar_roles_invalidos(roles)
        if len(invalidos) > 0:
            message = ' '.join(invalidos) if len(invalidos) > 1 else invalidos[0]
            raise ValidationError({"Error": message})
        return super().is_valid(raise_exception=raise_exception)

    # Convierte los valores de la lista de roles para que tenga los nombres de los roles.
    def convertir_lista_roles(self, roles):
        lista = []
        for rol in roles:
            if isinstance(rol, dict):
                nombre = rol["nombre"]
                lista.append(nombre)
            if isinstance(rol, str):
                lista.append(rol)
        return lista

    # Método que devuelve los datos del usuario. Quito la contraseña para que no sea mostrada al usuario.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['password'] = ""
        return ret

    # Método de creación de un usuario.
    def create(self, validated_data):
        user = Usuario.objects.create_user(**validated_data)
        user.token_email = secrets.token_hex(16)
        user.save()
        Token.objects.create(user=user)
        return user


# Verifica que los roles sean válidos.
def comprobar_roles_invalidos(roles):
    errores = []
    for rol in roles:
        rolValido = False
        for valido in Rol.ROLES:
            if valido == rol:
                rolValido = True
                break
        if rolValido is False:
            errores.append("No se ha encontrado el rol " + rol + ". ")
    return errores
