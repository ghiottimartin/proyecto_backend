from rest_framework import serializers
from rest_framework.authtoken.views import Token
from rest_framework.exceptions import ValidationError
from .models import Producto, Usuario, Rol

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'

class UsuarioSerializer(serializers.ModelSerializer):
    roles = RolSerializer(many=True, read_only=True)

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'roles']

    def is_valid(self, raise_exception):
        roles = self.context["roles"]
        invalidos = comprobar_roles_invalidos(roles)
        if len(invalidos) > 0:
            message = ' '.join(invalidos) if len(invalidos) > 1 else invalidos[0]
            raise ValidationError({"Error":message})            
        return super().is_valid(raise_exception=raise_exception)

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