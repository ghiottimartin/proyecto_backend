import datetime
from django.core.exceptions import ValidationError
from django.db import models
from base.models import Auditoria, Usuario
from producto.models import Producto


class Mesa(Auditoria, models.Model):
    """
        Representa una mesa que posee turnos.
    """

    OCUPADA = "ocupada"
    DISPONIBLE = "disponible"

    numero = models.BigIntegerField()
    estado = models.CharField(max_length=10, default=DISPONIBLE)
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

    def get_estado_texto(self):
        """
            Devuelve el estado en formato legible para el usuario.
            @return:
        """
        estado = self.estado.capitalize()
        return estado

    def get_estado_clase(self):
        """
            Devuelve la clase css del estado de la mesa.
            @return:
        """
        clase = "font-weight-bold badge"
        estado = self.estado
        if estado == Mesa.OCUPADA:
            clase = clase + " badge-danger"
        if estado == Mesa.DISPONIBLE:
            clase = clase + " badge-success"
        return clase

    def comprobar_puede_borrarse(self):
        """
            Comprueba si la mesa puede borrarse, para ello verifica que no tenga turnos.
            @return: bool
        """
        turnos = self.turnos.all().count()
        return turnos == 0

    def comprobar_puede_editarse(self):
        """
            Comprueba si la mesa puede editarse, para ello verifica que tenga estado disponible.
            @return: bool
        """
        estado = self.estado
        disponible = estado == Mesa.DISPONIBLE
        return disponible

    def crear_turno(self, nombre):
        """
            Crea un turno para la mesa actual, si el último turno de la mesa ya tiene un mozo se lo asigna al turno.
            Luego cambia el estado de la meza a ocupada.
            @return: Turno
        """
        try:
            mozo = Usuario.objects.get(first_name=nombre)
        except Usuario.DoesNotExist:
            mozo = None
        if mozo is None:
            raise ValidationError({"Error": "No se ha encontrado el mozo del turno."})
        turno = Turno(mesa=self, mozo=mozo)
        turno.save()

        self.estado = Mesa.OCUPADA
        self.save()
        return turno


class Turno(Auditoria, models.Model):
    """
        Representa un turno de una mesa.
    """

    class Meta:
        db_table = 'mesas_turnos'

    ABIERTO = "abierto"
    CERRADO = "cerrado"

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name="turnos")
    mozo = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="+", null=True)
    hora_inicio = models.DateTimeField(default=datetime.datetime.now)
    hora_fin = models.DateTimeField(null=True)

    def comprobar_abierto(self):
        """
            Comprueba si el turno está abierto, para ello verifica que la última hora sea None.
            @return: bool
        """
        hora_fin = self.hora_fin
        return hora_fin is None

    def comprobar_cerrado(self):
        """
            Comprueba si el turno está cerrado, para ello verifica que tenga hora de cierre.
            @return: bool
        """
        hora_fin = self.hora_fin
        return hora_fin is not None


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
