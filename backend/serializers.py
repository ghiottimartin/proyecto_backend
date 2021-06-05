from rest_framework import serializers
from rest_framework.authtoken.views import Token
from .models import Producto, Usuario, Rol


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name']

    extra_kwargs = {
        'password': {
            'write_only': True,
            'required': True,
        }
    }

    def create(self, validated_data):
        user = Usuario.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user
