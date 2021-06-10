from rest_framework import serializers
from rest_framework.authtoken.views import Token
from rest_framework.exceptions import ValidationError
from .models import Usuario, Rol
import secrets
from . import respuestas


class CustomModelSerializer(serializers.ModelSerializer):

    def get_errores_lista(self, errores=None):
        mensajes = []
        if errores is None:
            errores = self.errors
        for key in errores:
            error = errores[key][0]
            clave_ucfirst = key[0].upper() + key[1:]
            if isinstance(error, str):
                ucfirst = error[0].upper() + error[1:]
                texto = clave_ucfirst + ": " + ucfirst
                mensajes.append(texto)
            elif isinstance(error, dict):
                recursivos = self.get_errores_lista(error)
                mensajes = mensajes + recursivos
        return mensajes


class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'


class UsuarioSerializer(CustomModelSerializer):
    roles = RolSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'roles', 'habilitado', 'password', 'dni']

    def is_valid(self, raise_exception=False):
        roles = self.context["roles"]
        if isinstance(roles, list):
            roles = self.convertir_lista_roles(roles)
        invalidos = comprobar_roles_invalidos(roles)
        if len(invalidos) > 0:
            message = ' '.join(invalidos) if len(invalidos) > 1 else invalidos[0]
            raise ValidationError({"Error": message})
        return super().is_valid(raise_exception=raise_exception)

    def convertir_lista_roles(self, roles):
        lista = []
        for rol in roles:
            if isinstance(rol, dict):
                nombre = rol["nombre"]
                lista.append(nombre)
        return lista

    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['password'] = ""
        return ret

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
