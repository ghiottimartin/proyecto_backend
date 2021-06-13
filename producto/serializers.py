from rest_framework import serializers
from .models import Producto, Categoria
from backend.serializers import CustomModelSerializer


class ProductoSerializer(CustomModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'
