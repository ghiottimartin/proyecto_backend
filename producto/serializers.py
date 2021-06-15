from rest_framework import serializers
from .models import Producto, Categoria
from base.serializers import CustomModelSerializer
import locale
locale.setlocale(locale.LC_ALL, '')


class ProductoSerializer(CustomModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

    # Método que devuelve los datos del usuario. Quito la contraseña para que no sea mostrada al usuario.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['categoria'] = instance.categoria.nombre
        ret['precio_vigente'] = locale.currency(instance.precio_vigente)
        return ret


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
