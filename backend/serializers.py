from rest_framework import serializers
from .models import Producto
from django.contrib.auth.models import User
from rest_framework.authtoken.views import Token


class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name']

    extra_kwargs = {
        'password': {
            'write_only': True,
            'required': True,
        }
    }

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        Token.objects.create(user=user)
        return user
