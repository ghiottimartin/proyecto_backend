from base.serializers import CustomModelSerializer
from base.signals import get_usuario_logueado
from .models import Producto, Categoria, Ingreso, IngresoLinea, MovimientoStock
from rest_framework import serializers

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
        ret['categoria_texto'] = instance.categoria.nombre
        ret['precio_texto'] = locale.currency(instance.precio_vigente)
        return ret


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class IngresoLineaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = IngresoLinea
        fields = ['id', 'cantidad', 'producto', 'precio', 'total']

    # Método que devuelve los datos de la línea.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['precio_texto'] = locale.currency(instance.precio)
        ret['total_texto'] = locale.currency(instance.total)
        return ret


class IngresoSerializer(serializers.ModelSerializer):
    lineas = IngresoLineaSerializer(many=True, read_only=True)

    class Meta:
        model = Ingreso
        fields = '__all__'

    # Método que devuelve los datos del ingreso.
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id_texto'] = "I" + str(instance.id).zfill(5)
        ret['usuario_email'] = instance.usuario.email
        ret['usuario_nombre'] = instance.usuario.first_name
        ret['fecha_texto'] = instance.fecha.strftime('%d/%m/%Y %H:%M')
        ret['total_texto'] = locale.currency(instance.total)
        return ret


class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoStock
        fields = '__all__'


