import datetime
from django.core.exceptions import ValidationError
from django.db import models
from base.models import Auditoria, Usuario
from gastronomia.models import Venta, VentaLinea, Pedido
import pandas as pd
from producto.models import Producto
from producto.repositorio import get_producto
import locale


class Mesa(Auditoria, models.Model):
    """
        Representa una mesa que posee turnos.
    """

    OCUPADA = "ocupada"
    DISPONIBLE = "disponible"

    numero = models.BigIntegerField()
    estado = models.CharField(max_length=10, default=DISPONIBLE)
    descripcion = models.CharField(max_length=100, default="")

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

    def get_color_fondo(self):
        """
            Devuelve el color de fondo de la mesa. Si esta ocupada es rojo claro, sino es verde claro.
            @return: str
        """
        estado = self.estado
        if estado == self.DISPONIBLE:
            return "rgb(40 167 69 / 20%)"
        return "rgb(220 53 69 / 20%)"

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
    CANCELADO = "cancelado"

    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name="turnos")
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="+", null=True)
    mozo = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="+", null=True)
    estado = models.CharField(max_length=30, default=ABIERTO)
    hora_inicio = models.DateTimeField(default=datetime.datetime.now)
    hora_fin = models.DateTimeField(null=True)

    def comprobar_abierto(self):
        """
            Comprueba si el turno está abierto, para ello verifica que la última hora sea None y tenga estado abierto.
            @return: bool
        """
        hora_fin = self.hora_fin
        estado = self.estado
        return hora_fin is None and estado == self.ABIERTO

    def comprobar_cerrado(self):
        """
            Comprueba si el turno está cerrado, para ello verifica que tenga hora de cierre y tenga estado cerrado.
            @return: bool
        """
        hora_fin = self.hora_fin
        estado = self.estado
        return hora_fin is not None and estado == self.CERRADO

    def comprobar_cancelado(self):
        """
            Devuelve true si el turno está cancelado.
            @return: bool
        """
        estado = self.estado
        return estado == self.CANCELADO

    def comprobar_puede_cerrar(self):
        """
            Devuelve true si el turno puede cerrarse. Para ello debe tener al menos un producto cargado.
            @return: bool
        """
        cantidad_ordenes = self.ordenes.count()
        return cantidad_ordenes > 0

    def borrar_orden_por_id_producto(self, id_producto):
        """
            Borra la orden de producto según el id de producto.
            @param id_producto: int
            @return: None
        """
        orden = self.get_orden_por_id_producto(id_producto)
        if orden is not None:
            orden.delete()

    def borrar_ordenes_no_existentes(self, nuevos):
        """
            Borra las órdenes que no se encuentren dentro de la lista de ids de productos.
            @param nuevos: List
            @return: None
        """
        anteriores = self.get_ids_productos_anteriores()
        for anterior in anteriores:
            no_existe = anterior not in nuevos
            if no_existe:
                self.borrar_orden_por_id_producto(anterior)

    def agregar_editar_ordenes(self, ordenes):
        """
            Agrega o edita las órdenes del turno.
            @param ordenes: List
            @return: None
        """
        # Borro las órdenes eliminadas por el usuario.
        df_productos = pd.DataFrame(ordenes)
        nuevos_productos = df_productos['producto'].tolist()
        df_ids_productos = pd.DataFrame(nuevos_productos)
        nuevos = df_ids_productos['id'].tolist()
        self.borrar_ordenes_no_existentes(nuevos)

        # Actualizo o creo las órdenes.
        for orden in ordenes:
            id_producto = orden["producto"]["id"]
            cantidad = orden["cantidad"]
            producto = get_producto(id_producto)
            if producto is None:
                raise ValidationError("No se ha encontrado el producto a agregar al turno.")
            existe = self.get_orden_por_producto(producto)

            entregado = int(orden["entregado"]) if "entregado" in orden else 0
            if isinstance(existe, OrdenProducto):
                existe.cantidad = cantidad
                existe.entregado = entregado
                existe.save()
            else:
                orden = OrdenProducto(turno=self, producto=producto, cantidad=cantidad, entregado=entregado)
                orden.save()

    def get_ids_productos_anteriores(self):
        """
            Devuelve los ids de los productos del turno actual.
            @return: List
        """
        ordenes = self.ordenes.all()
        productos = []
        for orden in ordenes:
            producto = orden.producto
            productos.append(producto.id)
        return productos

    def get_orden_por_producto(self, producto):
        """
            Devuelve una orden filtrando por producto de la misma.
            @param producto: Producto
            @return: OrdenProducto|None
        """
        orden = self.ordenes.filter(producto=producto).first()
        return orden

    def get_orden_por_id_producto(self, id_producto):
        """
            Devuelve una orden filtrando por el id del producto.
            @param id_producto: int
            @return: OrdenProducto|None
        """
        orden = self.ordenes.filter(producto__id=id_producto).first()
        return orden

    def cancelar(self):
        """
            Cancela el turno actual.
            @return: None
        """
        self.estado = self.CANCELADO
        self.hora_fin = datetime.datetime.now()
        self.save()
        mesa = self.mesa
        mesa.estado = Mesa.DISPONIBLE
        mesa.save()

    def get_razon_no_puede_cerrar(self):
        """
            Devuelve el mensaje por el cual no puede cerrar la mesa.
            @return: str
        """
        mensaje = ""
        ordenes = self.ordenes.count()
        if ordenes == 0:
            mensaje = "Debe al menos tener un producto cargado."
        return mensaje

    def cerrar(self):
        """
            Cierra el turno de la mesa actual, dejándolo en estado cerrado y la mesa en estado disponible. Luego de
            cerrarlo crea la venta correspondiente.
            @return: None
        """
        self.estado = Turno.CERRADO
        self.hora_fin = datetime.datetime.now()
        self.save()

        mesa = self.mesa
        mesa.estado = Mesa.DISPONIBLE
        mesa.save()

        usuario = self.auditoria_creador
        venta = Venta(usuario=usuario, tipo=Venta.MESA, turno=self)
        venta.save()

        ordenes = self.ordenes.all()
        for orden in ordenes:
            orden.estado = OrdenProducto.ENTREGADO
            orden.save()

            producto = orden.producto
            cantidad = orden.cantidad
            precio = producto.precio_vigente
            total = precio * cantidad
            linea = VentaLinea(venta=venta, producto=producto, cantidad=cantidad, precio=precio, total=total)
            linea.save()

        venta.actualizar()
        venta.save()

        self.venta = venta
        self.save()

    def get_hora_inicio_texto(self):
        """
            Devuelve la hora que se inicio el turno.
            @return: str (HH:mm)
        """
        return self.hora_inicio.strftime('%H:%M')

    def get_hora_fin_texto(self):
        """
            Devuelve la hora que se inicio el turno.
            @return: str (HH:mm)
        """
        hora_fin = self.hora_fin
        if hora_fin is None:
            return "--"
        return self.hora_inicio.strftime('%H:%M')

    def get_estado_texto(self):
        """
            Devuelve el estado en formato legible para el usuario.
            @return:
        """
        estado = self.estado.capitalize()
        return estado

    def get_estado_clase(self):
        """
            Devuelve la clase css del estado del turno.
            @return:
        """
        clase = "font-weight-bold badge"
        estado = self.estado
        if estado == Turno.CANCELADO:
            clase = clase + " badge-danger"
        if estado == Turno.ABIERTO:
            clase = clase + " badge-success"
        if estado == Turno.CERRADO:
            clase = clase + " badge-primary"
        return clase

    def get_color_fondo(self):
        """
            Devuelve el color de fondo del turno.
            @return: str
        """
        estado = self.estado
        if estado == self.ABIERTO:
            return "rgb(40 167 69 / 20%)"
        if estado == self.CANCELADO:
            return "rgb(220 53 69 / 20%)"
        return "rgb(0 123 255 / 20%)"

    def get_total(self):
        total = 0
        ordenes = self.ordenes.all()
        for orden in ordenes:
            total += orden.get_total()
        return total

    def get_total_texto(self):
        """
            Devuelve el total en formato de texto.
            @return: str
        """
        total = self.get_total()
        return locale.currency(total)


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
    cantidad = models.IntegerField()
    entregado = models.IntegerField(default=0)

    def get_total(self):
        """
            Devuelve el total de la orden multiplicando el precio del producto por la cantidad.
            @return: decimal
        """
        producto = self.producto
        cantidad = self.cantidad
        precio = producto.precio_vigente
        return precio * cantidad

    def get_total_texto(self):
        """
            Devuelve el total en formato de texto.
            @return: str
        """
        total = self.get_total()
        return locale.currency(total)
