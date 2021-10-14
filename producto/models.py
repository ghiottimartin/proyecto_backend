import datetime
from django.db import models
from django.utils.translation import gettext_lazy as _
from base.models import Auditoria, Usuario
from gastronomia.models import Pedido, Estado
import uuid


class Categoria(Auditoria, models.Model):
    superior = models.ForeignKey(
        'Categoria', on_delete=models.PROTECT, related_name="inferiores", null=True, blank=True)
    nombre = models.CharField(max_length=30)
    descripcion = models.CharField(max_length=255, null=True)
    habilitado = models.BooleanField(default=True)
    borrado = models.BooleanField(default=False)

    def comprobar_puede_borrarse(self):
        cantidad = self.productos.all().filter(borrado=False).count()
        return cantidad == 0

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
    costo_vigente = models.FloatField()
    precio_vigente = models.FloatField()
    habilitado = models.BooleanField(default=True)
    borrado = models.BooleanField(default=False)
    stock = models.IntegerField(default=0)
    compra_directa = models.BooleanField(default=True)

    # Actualiza el precio vigente y agrego el precio a la colección de precios.
    def agregar_precio(self, nuevo=None):
        anterior = self.precio_vigente
        if nuevo is not None and round(anterior, 2) != round(nuevo, 2):
            self.precio_vigente = nuevo
            self.save()
        elif nuevo is None:
            nuevo = anterior

        ultimo = self.precios.last()
        ultimo_precio = ultimo.precio if ultimo is not None else anterior
        if ultimo_precio != nuevo or ultimo is None:
            precio = Precio(producto=self, precio=self.precio_vigente)
            precio.save()
            self.precios.add(precio)

    # Actualiza el costo vigente y agrego el costo a la colección de costos.
    def agregar_costo(self, nuevo=None):
        anterior = self.costo_vigente
        if nuevo is not None and round(anterior, 2) != round(nuevo, 2):
            self.costo_vigente = nuevo
            self.save()
        elif nuevo is None:
            nuevo = anterior

        ultimo = self.costos.last()
        ultimo_costo = ultimo.costo if ultimo is not None else anterior
        if ultimo_costo != nuevo or ultimo is None:
            costo = Costo(producto=self, costo=self.costo_vigente)
            costo.save()
            self.costos.add(costo)

    # Comprueba que el costo sea menor que el precio.
    def comprobar_producto_costo_validos(self, costo=None, precio=None):
        if costo is None:
            costo = self.costo_vigente
        if precio is None:
            precio = self.precio_vigente
        valido = precio > costo
        return valido

    # Comprueba que el producto pueda borrarse
    def comprobar_puede_borrarse(self):
        cantidad = Pedido.objects.all().filter(lineas__producto__exact=self).count()
        return cantidad == 0

    def get_margen_ganancia(self):
        precio = self.precio_vigente
        costo = self.costo_vigente
        diferencia = precio - costo
        margen = diferencia * 100 / precio
        redondeado = str(round(margen, 2))
        return redondeado + "%"

    def __str__(self):
        return self.nombre


class Precio(Auditoria, models.Model):
    producto = models.ForeignKey('producto.Producto', on_delete=models.CASCADE, related_name="precios")
    fecha = models.DateTimeField(default=datetime.datetime.now)
    precio = models.FloatField()

    def __str__(self):
        return self.producto.__str__() + ": $ " + self.precio.__str__()


class Costo(Auditoria, models.Model):
    producto = models.ForeignKey('producto.Producto', on_delete=models.CASCADE, related_name="costos")
    fecha = models.DateTimeField(default=datetime.datetime.now)
    costo = models.FloatField()

    def __str__(self):
        return self.producto.__str__() + ": $ " + self.costo.__str__()


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

    # Actualiza el total del ingreso a partir del total de cada línea.
    def actualizar_total(self):
        lineas = self.lineas.all()
        total = 0
        for linea in lineas:
            total += linea.total
        self.total = total
        self.save()

    # Crea un movimiento de stock por cada producto ingresado.
    def crear_movimientos(self):
        lineas = self.lineas.all()
        for linea in lineas:
            linea.crear_movimiento()

    # Devuelve true si el usuario puede visualizar el ingreso.
    def comprobar_puede_visualizar(self, usuario):
        es_admin = usuario.esAdmin
        return es_admin

    def __str__(self):
        return "Ingreso " + self.auditoria_creado_fecha.__str__()


class IngresoLinea(models.Model):
    ingreso = models.ForeignKey('producto.Ingreso', on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey('producto.Producto', on_delete=models.PROTECT, related_name="+")
    cantidad = models.IntegerField()
    costo = models.IntegerField()
    total = models.FloatField(default=0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.actualizar_total()
        self.actualizar_costo_producto()

    # Crea un movimiento de stock a partir del producto ingresado.
    def crear_movimiento(self):
        producto = self.producto
        cantidad = self.cantidad
        movimiento = MovimientoStock(producto=producto, cantidad=cantidad)
        movimiento.save()

        stock = producto.stock
        nuevo = stock + cantidad
        producto.stock = nuevo
        producto.save()

    # Actualiza el total de la línea a partir de la cantidad y el precio.
    def actualizar_total(self):
        costo = self.costo
        total = costo * self.cantidad
        self.total = total
        self.save()

    # Si el costo del producto cambió se lo actualiza.
    def actualizar_costo_producto(self):
        producto = self.producto
        costo = round(self.costo, 2)
        costo_producto = round(producto.costo_vigente, 2)

        precio = producto.precio_vigente
        if costo > precio:
            costo = precio
        if costo != costo_producto:
            producto.agregar_costo(costo)

    def __str__(self):
        return "Línea de " + self.ingreso.__str__()
