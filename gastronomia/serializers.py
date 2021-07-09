from rest_framework import serializers
from .models import Pedido, PedidoLinea
from producto.serializers import ProductoSerializer


class LineaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    class Meta:
        model = PedidoLinea
        fields = ['id', 'cantidad', 'subtotal', 'producto']


class PedidoSerializer(serializers.ModelSerializer):
    lineas = LineaSerializer(many=True, read_only=True)

    class Meta:
        model = Pedido
        fields = '__all__'
