from rest_framework import serializers
from .models import Producto
from django.contrib.auth.models import User
from rest_framework.authtoken.views import Token


class ProductoSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=30)
    precio = serializers.FloatField()

    def create(self, validated_data):
        return Producto.objects.create(validated_data)

    def update(self, instance, validated_data):
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.precio = validated_data.get('precio', instance.precio)
        instance.save()

        return instance


class ProductoModalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


class UsuarioSerializer(serializers.Serializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'password', 'first_name', 'email']

        extra_kwargs = {
            'password': {
                'required': True,
            }
        }

    def to_internal_value(self, data):
        internal_value = super(
            UsuarioSerializer, self).to_internal_value(data)
        del data['tipoRegistro']
        del data['password_confirmation']
        for key, value in data.items():
            internal_value.update({key: value})
        return internal_value

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
