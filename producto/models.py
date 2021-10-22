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
    auditoria_creador = models.ForeignKey('base.Usuario', on_delete=models.CASCADE, related_name="categorias_creadas", null=True)
    auditoria_modificado = models.ForeignKey('base.Usuario', on_delete=models.CASCADE, related_name="categorias_modificadas", null=True)

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
    nombre = models.CharField(max_length=50, unique=True)
    imagen = models.ImageField(_("Image"), upload_to=upload_to, null=True, default="producto/defecto/default.jpg")
    imagen_nombre = models.CharField(max_length=50, default="default.jpg")
    descripcion = models.CharField(max_length=255, default="")
    costo_vigente = models.FloatField()
    precio_vigente = models.FloatField()
    habilitado = models.BooleanField(default=True)
    borrado = models.BooleanField(default=False)
    stock = models.IntegerField(default=0)
    stock_seguridad = models.IntegerField(default=20)
    compra_directa = models.BooleanField(default=False)
    venta_directa = models.BooleanField(default=True)
    auditoria_creador = models.ForeignKey('base.Usuario', on_delete=models.CASCADE, related_name="productos_creados", null=True)
    auditoria_modificado = models.ForeignKey('base.Usuario', on_delete=models.CASCADE, related_name="productos_modificados", null=True)

    # Actualiza el precio vigente y agrego el precio a la colección de precios.
    def agregar_precio(self, nuevo=None):
        anterior = self.precio_vigente
        if nuevo is None:
            nuevo = anterior

        ultimo = self.precios.last()
        ultimo_precio = ultimo.precio if ultimo is not None else anterior
        if ultimo_precio != nuevo or ultimo is None:
            self.precio_vigente = nuevo
            self.save()
            precio = Precio(producto=self, precio=nuevo)
            precio.save()
            self.precios.add(precio)

    # Actualiza el costo vigente y agrego el costo a la colección de costos.
    def agregar_costo(self, nuevo=None):
        anterior = self.costo_vigente
        if nuevo is None:
            nuevo = anterior

        ultimo = self.costos.last()
        ultimo_costo = ultimo.costo if ultimo is not None else anterior
        if ultimo_costo != nuevo or ultimo is None:
            self.costo_vigente = nuevo
            self.save()
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

    # Comprueba que el producto tenga movimientos
    def comprobar_tiene_movimientos(self):
        cantidad = MovimientoStock.objects.filter(producto=self).count()
        return cantidad > 0

    # Comprueba que si hay que alertar de stock faltante.
    def comprobar_alerta_stock(self):
        actual = self.stock
        alerta = self.stock_seguridad
        return actual < alerta

    # Devuelve el margen de ganancia del producto.
    def get_margen_ganancia(self):
        precio = self.precio_vigente
        costo = self.costo_vigente
        diferencia = precio - costo
        margen = diferencia * 100 / precio
        redondeado = str(round(margen, 2))
        return redondeado + "%"

    # Actualiza el stock y sus movimientos en caso de ser necesario.
    def actualizar_stock(self, nueva=0, descripcion="", reemplazo_linea=None):
        if nueva == 0 and reemplazo_linea is None:
            return

        # Calculo la cantidad de stock generado por la edición.
        acumulado = 0
        movimientos = MovimientoStock.objects.filter(producto=self)
        for movimiento in movimientos:
            acumulado += movimiento.cantidad
        diferencia = nueva - acumulado

        # Si no hubo diferencia no hay que actualizar el stock
        if diferencia == 0:
            return

        if descripcion == "":
            descripcion = "Edición de stock del producto"

        # Si hubo diferencia se actualiza el stock
        movimiento = MovimientoStock(producto=self, cantidad=diferencia, descripcion=descripcion)
        if reemplazo_linea is not None and isinstance(reemplazo_linea, ReemplazoMercaderiaLinea):
            movimiento.reemplazo_linea = reemplazo_linea
        movimiento.save()

        self.stock = int(nueva)
        self.save()

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
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name="movimientos", default="movimientos")
    ingreso_linea = models.ForeignKey('producto.IngresoLinea', on_delete=models.CASCADE, related_name="movimientos", default=None, null=True)
    reemplazo_linea = models.ForeignKey('producto.ReemplazoMercaderiaLinea', on_delete=models.CASCADE, related_name="reemplazos", default=None, null=True)
    cantidad = models.IntegerField()
    descripcion = models.CharField(max_length=255)

    def __str__(self):
        return self.auditoria_creado_fecha.__str__()


class Ingreso(Auditoria, models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="ingresos")
    fecha = models.DateTimeField(default=datetime.datetime.now)
    total = models.FloatField(default=0)
    anulado = models.DateTimeField(null=True)

    def actualizar(self):
        self.actualizar_lineas()
        self.actualizar_total()

    def actualizar_lineas(self):
        lineas = self.lineas.all()
        for linea in lineas:
            linea.actualizar()

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

    # Devuelve true si el usuario puede anular el ingreso.
    def comprobar_puede_anular(self, usuario):
        es_admin = usuario.esAdmin
        anulado = self.comprobar_anulado()
        return es_admin and not anulado

    # Devuelve true si el usuario puede visualizar movimientos de stock del ingreso.
    def comprobar_puede_ver_movimientos(self, usuario):
        es_admin = usuario.esAdmin
        return es_admin

    # Comprueba que el ingreso tenga movimientos
    def comprobar_tiene_movimientos(self):
        cantidad = MovimientoStock.objects.filter(ingreso_linea__ingreso=self).count()
        return cantidad > 0

    # Devuelve true si ingreso no está anulado.
    def comprobar_anulado(self):
        anulado = self.anulado
        return anulado is not None

    # Anula el ingreso generando un movimiento de stock a los productos ingresados.
    def anular(self):
        self.anulado = datetime.datetime.now()
        lineas = self.lineas.all()
        for linea in lineas:
            linea.anular()

    # Devuelve la clase del estado del ingreso.
    def get_estado_clase(self):
        clase = 'font-weight-bold'
        anulado = self.comprobar_anulado()
        if anulado:
            clase += ' text-danger'
        else:
            clase += ' text-success'
        return clase

    # Devuelve la fecha de anulación del ingreso. En caso que no haya sido anulado devuelve string vacío.
    def get_fecha_anulado_texto(self):
        anulado = self.anulado
        if anulado is None:
            return ""
        return anulado.strftime('%d/%m/%Y %H:%M')

    # Devuelve el estado del ingreso. Puede ser activo o anulado.
    def get_estado_legible(self):
        anulado = self.comprobar_anulado()
        if anulado:
            return 'Anulado'
        return 'Activo'

    def __str__(self):
        return "Ingreso " + self.auditoria_creado_fecha.__str__()


class IngresoLinea(models.Model):
    ingreso = models.ForeignKey('producto.Ingreso', on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey('producto.Producto', on_delete=models.PROTECT, related_name="+")
    cantidad = models.IntegerField()
    costo = models.IntegerField()
    total = models.FloatField(default=0)

    # Crea un movimiento de stock a partir del producto ingresado.
    def crear_movimiento(self):
        producto = self.producto
        cantidad = self.cantidad
        id_texto = str(self.ingreso.id).zfill(5)
        descripcion = "Ingreso I" + id_texto
        movimiento = MovimientoStock(producto=producto, cantidad=cantidad, descripcion=descripcion, ingreso_linea=self)
        movimiento.save()

        stock = producto.stock
        nuevo = stock + cantidad
        producto.stock = nuevo
        producto.save()

    def actualizar(self):
        self.actualizar_total()
        self.actualizar_productos()

    # Actualiza el total de la línea a partir de la cantidad y el precio.
    def actualizar_total(self):
        costo = self.costo
        total = costo * self.cantidad
        self.total = total
        self.save()

    # Si el costo del producto cambió se lo actualiza.
    def actualizar_productos(self):
        producto = self.producto
        costo = round(self.costo, 2)
        costo_producto = round(producto.costo_vigente, 2)

        precio = producto.precio_vigente
        if costo > precio:
            producto.agregar_precio(nuevo=costo)
        if costo != costo_producto:
            producto.agregar_costo(nuevo=costo)

    # Crea un nuevo movimiento de stock negativo y actualiza el stock del producto.
    def anular(self):
        cantidad = self.cantidad
        producto = self.producto
        anterior = producto.stock
        nueva = anterior - cantidad
        if nueva < 0:
            nueva = 0

        producto.stock = nueva
        producto.save()

        cantidadAnulada = cantidad * -1
        id_texto = str(self.ingreso.id).zfill(5)
        descripcion = "Ingreso I" + id_texto + " anulado"
        movimiento = MovimientoStock(producto=producto, cantidad=cantidadAnulada, descripcion=descripcion, ingreso_linea=self)
        movimiento.save()

    def __str__(self):
        return "Línea de " + self.ingreso.__str__()


class ReemplazoMercaderia(Auditoria, models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="reemplazos")
    fecha = models.DateTimeField(default=datetime.datetime.now)
    anulado = models.DateTimeField(null=True)

    # Devuelve true si el usuario puede visualizar el reemplazo de mercadería.
    def comprobar_puede_visualizar(self, usuario):
        es_admin = usuario.esAdmin
        return es_admin

    # Devuelve true si el usuario puede anular el reemplazo de mercadería.
    def comprobar_puede_anular(self, usuario):
        es_admin = usuario.esAdmin
        anulado = self.comprobar_anulado()
        return es_admin and not anulado

    # Devuelve true si ingreso no está anulado.
    def comprobar_anulado(self):
        anulado = self.anulado
        return anulado is not None

    # Devuelve la clase del estado del reemplazo de mercadería.
    def get_estado_clase(self):
        clase = 'font-weight-bold'
        anulado = self.comprobar_anulado()
        if anulado:
            clase += ' text-danger'
        else:
            clase += ' text-success'
        return clase

    # Devuelve la fecha de anulación del reemplazo de mercadería. En caso que no haya sido anulado devuelve string vacío.
    def get_fecha_anulado_texto(self):
        anulado = self.anulado
        if anulado is None:
            return ""
        return anulado.strftime('%d/%m/%Y %H:%M')

    # Devuelve el estado del reemplazo de mercadería. Puede ser activo o anulado.
    def get_estado_legible(self):
        anulado = self.comprobar_anulado()
        if anulado:
            return 'Anulado'
        return 'Activo'

    # Devuelve el id en formato de texto del reemplazo de mercadería.
    def get_id_texto(self):
        return "RM" + str(self.id).zfill(5)

    # Genera los movimientos de movimientos de stock generados por los reemplazo de mercadería.
    def generar_movimientos(self):
        lineas = self.lineas.all()
        for linea in lineas:
            linea.crear_movimiento()

    # Anula el reemplazo de mercadería generando un movimiento de stock por productos reemplazados.
    def anular(self):
        self.anulado = datetime.datetime.now()
        lineas = self.lineas.all()
        for linea in lineas:
            linea.anular()

    def __str__(self):
        return "Reemplazo de mercadería " + self.auditoria_creado_fecha.__str__()


class ReemplazoMercaderiaLinea(models.Model):
    reemplazo = models.ForeignKey('producto.ReemplazoMercaderia', on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey('producto.Producto', on_delete=models.PROTECT, related_name="reemplazos")
    stock_anterior = models.IntegerField()
    stock_nuevo = models.IntegerField()
    reemplazo_completo = models.BooleanField(default=False)

    # Crea un movimiento de stock a partir del producto reemplazado.
    def crear_movimiento(self):
        producto = self.producto
        stock_nuevo = self.stock_nuevo

        id_texto = self.reemplazo.get_id_texto()
        descripcion = "Reemplazo de mercadería " + id_texto
        producto.actualizar_stock(nueva=stock_nuevo, descripcion=descripcion, reemplazo_linea=self)

    # Crea un nuevo movimiento de stock negativo y actualiza el stock del producto.
    def anular(self):
        anterior = self.stock_anterior
        producto = self.producto
        producto.actualizar_stock(nueva=anterior, reemplazo_linea=self)

    def __str__(self):
        return "Línea de " + self.reemplazo.__str__()
