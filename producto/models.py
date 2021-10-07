import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from base.models import Auditoria, Usuario
import uuid


class Categoria(Auditoria, models.Model):
    superior = models.ForeignKey(
        'Categoria', on_delete=models.PROTECT, related_name="inferiores", null=True, blank=True)
    nombre = models.CharField(max_length=30)
    descripcion = models.CharField(max_length=255, null=True)
    habilitado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


# Define la ruta y el nombre del archivo para la imagen de un producto.
def upload_to(instance, filename):
    return 'producto/{id}-{filename}'.format(id=uuid.uuid4(), filename=filename)


class Producto(Auditoria, models.Model):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos", default="productos")
    nombre = models.CharField(max_length=50)
    imagen = models.ImageField(_("Image"), upload_to=upload_to, null=True, default="producto/defecto/default.jpg")
    imagen_nombre = models.CharField(max_length=50, default="default.jpg")
    descripcion = models.CharField(max_length=255, default="")
    precio_vigente = models.FloatField()
    habilitado = models.BooleanField(default=True)
    borrado = models.BooleanField(default=False)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return self.nombre


class MovimientoStock(Auditoria, models.Model):
    producto = models.ForeignKey(
        Producto, on_delete=models.PROTECT, related_name="movimientos", default="movimientos")
    cantidad = models.IntegerField()

    def __str__(self):
        return self.auditoria_creado_fecha


class Ingreso(Auditoria, models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="+")
    fecha = models.DateTimeField(default=datetime.datetime.now)
    total = models.FloatField(default=0)

    def actualizar_total(self):
        lineas = self.lineas.all()
        total = 0
        for linea in lineas:
            total += linea.total
        self.total = total
        self.save()

    def crear_movimientos(self):
        lineas = self.lineas.all()
        for linea in lineas:
            linea.crear_movimiento()

    def __str__(self):
        return "Ingreso " + self.auditoria_creado_fecha.__str__()


class IngresoLinea(models.Model):
    ingreso = models.ForeignKey('producto.Ingreso', on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey('producto.Producto', on_delete=models.PROTECT, related_name="+")
    cantidad = models.IntegerField()
    precio = models.IntegerField()
    total = models.FloatField(default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.actualizar_total()

    def crear_movimiento(self):
        producto = self.producto
        cantidad = self.cantidad
        movimiento = MovimientoStock(producto=producto, cantidad=cantidad)
        movimiento.save()

        stock = producto.stock
        nuevo = stock + cantidad
        producto.stock = nuevo
        producto.save()

    def actualizar_total(self):
        # Mas adelante se va a actualizar el precio del producto.
        precio = self.precio
        total = precio * self.cantidad
        self.total = total
        self.save()

    def __str__(self):
        return "Línea de " + self.ingreso.__str__()
