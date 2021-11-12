from .models import Mesa, Turno, OrdenProducto
from base.serializers import UsuarioSerializer
from producto.serializers import ProductoSerializer
from rest_framework import serializers


class MesaSerializer(serializers.ModelSerializer):
    ultimo_turno = serializers.SerializerMethodField()

    class Meta:
        model = Mesa
        fields = ['id', 'numero', 'ultimo_turno', 'estado', 'descripcion']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['numero_texto'] = instance.get_numero_texto()
        ret['descripcion_texto'] = instance.get_descripcion_texto()
        ret['puede_borrarse'] = instance.comprobar_puede_borrarse()
        ret['estado_texto'] = instance.get_estado_texto()
        ret['estado_clase'] = instance.get_estado_clase()
        ret['puede_editarse'] = instance.comprobar_puede_editarse()
        return ret

    def get_ultimo_turno(self, objeto):
        """
            Devuelve el último turno de la mesa en formato json.
            @param objeto: Mesa
            @return: JSON<Turno>
        """
        ultimo = objeto.turnos.last()
        if ultimo is None:
            return None
        json = TurnoSerializer(instance=ultimo).data
        return json


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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['abierto'] = instance.comprobar_abierto()
        ret['cerrado'] = instance.comprobar_cerrado()
        return ret
