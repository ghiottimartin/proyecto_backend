from .models import Mesa
from base.serializers import UsuarioSerializer
from rest_framework import serializers


class MesaSerializer(serializers.ModelSerializer):
    mozos = UsuarioSerializer(many=True, read_only=True)

    class Meta:
        model = Mesa
        fields = ['id', 'numero', 'mozos', 'descripcion']

    # Método que devuelve los datos de la línea.
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['numero_texto'] = instance.get_numero_texto()
        return ret
