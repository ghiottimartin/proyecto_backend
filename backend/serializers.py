from rest_framework import serializers
from .models import Producto


class ProductoSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=30)
    precio = serializers.FloatField()

    def create(self, validated_data):
        return Producto.objects.create(validated_data)

    def update(self, instance, validated_data):
        instance.nombre = validated_data.get('nombre', instance.nombre)
        instance.precio = validated_data.get('precio', instance.precio)
        instance.save()

        return instance


class ProductoModalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        #fields = ('id', 'nombre', 'precio')
        fields = '__all__'
