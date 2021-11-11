import datetime

from django.db import models
from base.models import Auditoria, Usuario
from producto.models import Producto


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
        """
            Comprueba si la mesa puede borrarse, para ello verifica que no tenga turnos.
            @return: bool
        """
        turnos = self.turnos.all().count()
        return turnos == 0


class Turno(Auditoria, models.Model):
    """
        Representa un turno de una mesa.
    """

    class Meta:
        db_table = 'mesas_turnos'

    ABIERTO = "abierto"
    CERRADO = "cerrado"

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name="turnos")
    mozo = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="+")
    hora_inicio = models.DateTimeField(default=datetime.datetime.now)
    hora_fin = models.DateTimeField(default=datetime.datetime.now)


class OrdenProducto(models.Model):
    """
        Representa una producto pedido en un turno. Puede tener estado solicitado, cuando fue solicitado a la moza o
        entregado cuando ya fue entregado a la mesa.
    """

    class Meta:
        db_table = 'mesas_ordenes_productos'

    SOLICITADO = 'solicitado'
    ENTREGADO = 'entregado'

    turno = models.ForeignKey(Turno, on_delete=models.CASCADE, related_name="ordenes")
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="ordenes")
    estado = models.CharField(max_length=40, default=SOLICITADO)
