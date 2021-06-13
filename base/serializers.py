from rest_framework import serializers
from rest_framework.authtoken.views import Token
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
