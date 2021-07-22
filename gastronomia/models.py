from django.db import models
from base.models import Auditoria, Usuario
import datetime


class Estado(models.Model):
    pedido = models.ForeignKey('gastronomia.Pedido', on_delete=models.CASCADE, related_name="estados")
    estado = models.CharField(max_length=40)
    fecha = models.DateTimeField(default=datetime.datetime.now)

    ABIERTO = 'abierto'
    CERRADO = 'cerrado'
    FINALIZADO = 'finalizado'

    @classmethod
    def comprobar_estado_valido(cls, estado):
        return estado == cls.ABIERTO or estado == cls.CERRADO


class Pedido(Auditoria, models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="+")
    fecha = models.DateTimeField(default=datetime.datetime.now)
    ultimo_estado = models.CharField(max_length=40, default=Estado.ABIERTO)
    total = models.FloatField()
    forzar = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.save()
        self.agregar_estado(Estado.ABIERTO)

    def comprobar_vacio(self):
        cantidad_lineas = self.lineas.count()
        return cantidad_lineas == 0

    def comprobar_estado_cerrado(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.CERRADO

    def comprobar_estado_abierto(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.ABIERTO

    def comprobar_estado_finalizado(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.FINALIZADO

    def actualizar_total(self):
        lineas = self.lineas.all()
        total = 0
        for linea in lineas:
            total += linea.total
        self.total = total
        self.save()

    def agregar_estado(self, estado):
        ultimo = self.estados.order_by('-fecha').filter(estado=estado).first()
        if ultimo is None:
            objeto = Estado(estado=estado, pedido=self)
            objeto.save()
            self.ultimo_estado = estado
            self.estados.add(objeto)


    def borrar_datos_pedido(self):
        self.estados.all().delete()
        self.lineas.all().delete()
        self.save()

    def finalizar_pedido(self):
        self.agregar_estado(Estado.FINALIZADO)
        self.save()


class PedidoLinea(models.Model):
    pedido = models.ForeignKey('gastronomia.Pedido', on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey('producto.Producto', on_delete=models.PROTECT, related_name="+")
    cantidad = models.IntegerField()
    subtotal = models.FloatField()
    total = models.FloatField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.actualizar_total()

    def actualizar_total(self):
        precio = self.producto.precio_vigente
        total = precio * self.cantidad
        self.subtotal = precio
        self.total = total
        self.save()


