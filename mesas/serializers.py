from .models import Mesa, Turno, OrdenProducto
from base.serializers import UsuarioSerializer
from gastronomia.serializers import VentaSerializer, PedidoSerializer
from producto.serializers import ProductoSerializer
from rest_framework import serializers


class MesaSerializer(serializers.ModelSerializer):
    ultimo_turno = serializers.SerializerMethodField()

    class Meta:
        model = Mesa
        fields = ['id', 'numero', 'ultimo_turno', 'estado', 'descripcion']

    def to_representation(self, mesa):
        ret = super().to_representation(mesa)
        ret['numero_texto'] = mesa.get_numero_texto()
        ret['descripcion_texto'] = mesa.get_descripcion_texto()
        ret['puede_borrarse'] = mesa.comprobar_puede_borrarse()
        ret['estado_texto'] = mesa.get_estado_texto()
        ret['estado_clase'] = mesa.get_estado_clase()
        ret['color_fondo'] = mesa.get_color_fondo()
        ret['puede_editarse'] = mesa.comprobar_puede_editarse()
        ret['disponible'] = mesa.comprobar_estado_disponible()
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

    class Meta:
        model = OrdenProducto
        fields = '__all__'

    def to_representation(self, orden):
        ret = super().to_representation(orden)
        ret['total_texto'] = orden.get_total_texto()
        ret['cantidad_anterior'] = orden.cantidad
        return ret


class TurnoSerializer(serializers.ModelSerializer):
    mozo = UsuarioSerializer(read_only=True)
    venta = VentaSerializer(read_only=True)
    pedido = PedidoSerializer(read_only=True)
    ordenes = OrdenProductoSerializer(read_only=True, many=True)

    class Meta:
        model = Turno
        fields = '__all__'

    def to_representation(self, turno):
        ret = super().to_representation(turno)
        ret['fecha'] = turno.hora_inicio.strftime('%d/%m/%Y')
        ret['hora_inicio_texto'] = turno.get_hora_inicio_texto()
        ret['hora_fin_texto'] = turno.get_hora_fin_texto()
        ret['abierto'] = turno.comprobar_abierto()
        ret['cerrado'] = turno.comprobar_cerrado()
        ret['estado_texto'] = turno.get_estado_texto()
        ret['estado_clase'] = turno.get_estado_clase()
        ret['color_fondo'] = turno.get_color_fondo()
        ret['total_texto'] = turno.get_total_texto()
        ret['mesa_numero'] = turno.mesa.get_numero_texto()
        return ret
