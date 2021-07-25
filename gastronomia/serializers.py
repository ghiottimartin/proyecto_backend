from rest_framework import serializers
from .models import Pedido, PedidoLinea
from producto.serializers import ProductoSerializer
from base.signals import get_usuario_logueado

import locale
locale.setlocale(locale.LC_ALL, '')


class LineaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    class Meta:
        model = PedidoLinea
        fields = ['id', 'cantidad', 'subtotal', 'producto', 'total']

    # Método que devuelve los datos de la línea.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['subtotal_texto'] = locale.currency(instance.subtotal)
        ret['total_texto'] = locale.currency(instance.total)
        return ret


class PedidoSerializer(serializers.ModelSerializer):
    lineas = LineaSerializer(many=True, read_only=True)
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = '__all__'

    # Método que devuelve los datos del pedido.
    def to_representation(self, instance):
        logueado = get_usuario_logueado()

        ret = super().to_representation(instance)
        ret['id_texto'] = "P" + str(instance.id).zfill(5)
        ret['fecha_texto'] = instance.fecha.strftime('%d/%m/%Y %H:%M')
        ret['total_texto'] = locale.currency(instance.total)
        ret['estado_texto'] = instance.ultimo_estado.capitalize()
        ret['usuario_texto'] = instance.usuario.email
        ret['mostrar_usuario'] = logueado.esAdmin or logueado.esVendedor
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

        puede_cerrar = objeto.comprobar_puede_cerrar(logueado)
        if puede_cerrar:
            accion = 'recibir'
            operaciones.append({
                'accion': 'recibir',
                'clase': 'btn btn-sm btn-success text-success',
                'texto': 'Entregar',
                'icono': 'fa fa-check-circle',
                'key': str(objeto.id) + "-" + accion,
            })

        puede_cancelar = objeto.comprobar_puede_cancelar(logueado)
        if puede_cancelar:
            accion = 'cancelar'
            operaciones.append({
                'accion': 'cancelar',
                'clase': 'btn btn-sm btn-danger text-danger',
                'texto': 'Cancelar',
                'icono': 'fa fa-window-close',
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones
