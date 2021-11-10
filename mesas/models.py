from django.db import models
from base.models import Auditoria, Usuario


class Mesa(Auditoria, models.Model):
    """
        Representa una mesa que posee turnos.
    """

    OCUPADA = "ocupada"
    DESOCUPADA = "desocupada"

    numero = models.BigIntegerField()
    estado = models.CharField(max_length=10, default=DESOCUPADA)
    descripcion = models.CharField(max_length=100)

    def get_numero_texto(self):
        """
            Devuelve el número legible de la mesa en formato #00052
        """
        numero = self.numero
        return "#" + str(numero).zfill(5)

    def get_descripcion_texto(self):
        """
            Devuelve la descripción de la mesa, si no tiene devuelve 'Sin observaciones'.
        """
        descripcion = self.descripcion
        tiene_descripcion = len(descripcion) > 0
        if not tiene_descripcion:
            return "Sin observaciones"
        return descripcion

    def comprobar_puede_borrarse(self):
        # Falta implementar la comprobación de si tiene turnos.
        return True
