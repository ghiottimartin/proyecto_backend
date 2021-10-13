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

    # Método que devuelve los datos del producto
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['categoria_texto'] = instance.categoria.nombre
        ret['precio_texto'] = locale.currency(instance.precio_vigente)
        ret['costo_texto'] = locale.currency(instance.costo_vigente)
        ret['margen_texto'] = instance.get_margen_ganancia()
        ret['puede_borrarse'] = instance.comprobar_puede_borrarse()
        return ret


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'

    # Método que devuelve los datos de la categoría del producto.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['puede_borrarse'] = instance.comprobar_puede_borrarse()
        return ret


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
    operaciones = serializers.SerializerMethodField()

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

    def get_operaciones(self, objeto):
        logueado = get_usuario_logueado()
        operaciones = []

        puede_visualizar = objeto.comprobar_puede_visualizar(logueado)
        if puede_visualizar:
            accion = 'visualizar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-info text-info',
                'texto': 'Ver',
                'icono': 'fa fa-eye',
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones


class MovimientoSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimientoStock
        fields = '__all__'


