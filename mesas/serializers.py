from .models import Mesa, Turno, OrdenProducto
from base.serializers import UsuarioSerializer
from producto.serializers import ProductoSerializer
from rest_framework import serializers


class MesaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mesa
        fields = ['id', 'numero', 'descripcion']

    # Método que devuelve los datos de la línea.
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['numero_texto'] = instance.get_numero_texto()
        ret['descripcion_texto'] = instance.get_descripcion_texto()
        ret['puede_borrarse'] = instance.comprobar_puede_borrarse()
        ret['estado_texto'] = instance.get_estado_texto()
        ret['estado_clase'] = instance.get_estado_clase()
        return ret


class OrdenProductoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Mesa:
        model = OrdenProducto
        fields = '__all__'


class TurnoSerializer(serializers.ModelSerializer):
    mozo = UsuarioSerializer(read_only=True)
    ordenes = OrdenProductoSerializer(read_only=True, many=True)

    class Meta:
        model = Turno
        fields = '__all__'
