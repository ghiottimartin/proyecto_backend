from .models import Mesa
from base.serializers import UsuarioSerializer
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
        return ret
