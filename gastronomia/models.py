from django.db import models
from base.models import Auditoria, Usuario
import datetime


class Estado(models.Model):
    pedido = models.ForeignKey('gastronomia.Pedido', on_delete=models.CASCADE, related_name="estados")
    estado = models.CharField(max_length=40)
    fecha = models.DateTimeField(default=datetime.datetime.now)

    ABIERTO = 'abierto'
    EN_CURSO = 'en curso'
    DISPONIBLE = 'disponible'
    RECIBIDO = 'recibido'
    ANULADO = 'anulado'
    ENTREGADO = 'entregado'

    # Comprueba si el estado es válido
    @classmethod
    def comprobar_estado_valido(cls, estado):
        return estado == cls.ABIERTO or estado == cls.EN_CURSO or estado == cls.RECIBIDO or estado == cls.ANULADO \
               or estado == cls.ENTREGADO or estado == cls.DISPONIBLE


class Pedido(Auditoria, models.Model):
    TIPO_RETIRO = 'retiro'
    TIPO_DELIVERY = 'delivery'

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="pedidos")
    venta = models.ForeignKey("gastronomia.Venta", on_delete=models.CASCADE, related_name="+", null=True)
    fecha = models.DateTimeField(default=datetime.datetime.now)
    ultimo_estado = models.CharField(max_length=40, default=Estado.ABIERTO)
    total = models.FloatField()
    forzar = models.BooleanField(default=False)
    cambio = models.FloatField(default=0)
    observaciones = models.CharField(max_length=255, default="")
    tipo = models.CharField(max_length=30, default=TIPO_RETIRO, blank=True)
    direccion = models.CharField(max_length=255, default="", blank=True)

    # Comprueba que el pedido esté vacío, es decir no tenga líneas.
    def comprobar_vacio(self):
        cantidad_lineas = self.lineas.count()
        return cantidad_lineas == 0

    # Devuelve true si el estado del pedido es en curso.
    def comprobar_estado_en_curso(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.EN_CURSO

    # Devuelve true si el estado del pedido es abierto.
    def comprobar_estado_abierto(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.ABIERTO

    # Devuelve true si el estado del pedido es recibido.
    def comprobar_estado_recibido(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.RECIBIDO

    # Devuelve true si el estado del pedido es anulado.
    def comprobar_estado_anulado(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.ANULADO

    # Devuelve true si el estado del pedido es disponible.
    def comprobar_estado_disponible(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.DISPONIBLE

    # Devuelve true si el usuario actual puede visualizar el pedido.
    def comprobar_puede_visualizar(self, usuario):
        es_admin = usuario.esAdmin
        es_vendedor = usuario.esVendedor
        pedido_usuario = self.usuario
        le_pertenece = pedido_usuario == usuario
        return le_pertenece or es_admin or es_vendedor

    # Devuelve true si el usuario actual puede entregar el pedido.
    def comprobar_puede_entregar(self, usuario):
        disponible = self.comprobar_estado_disponible()
        es_vendedor = usuario.esVendedor
        return disponible and es_vendedor

    # Devuelve true si el usuario actual puede anular el pedido.
    def comprobar_puede_anular(self, usuario):
        abierto = self.comprobar_estado_abierto()
        en_curso = self.comprobar_estado_en_curso()
        disponible = self.comprobar_estado_disponible()
        es_vendedor = usuario.esVendedor
        pedido_usuario = self.usuario
        le_pertenece = pedido_usuario == usuario
        return ((en_curso or disponible) and es_vendedor) or (le_pertenece and (abierto or en_curso or disponible))

    # Devuelve true si el pedido puese ser marcado como disponible para ser retirado.
    def comprobar_puede_marcar_disponible(self, usuario):
        en_curso = self.comprobar_estado_en_curso()
        es_vendedor = usuario.esVendedor
        return en_curso and es_vendedor

    def comprobar_puede_emitir_comanda(self, usuario):
        """
            Devuelve true si se puede imprimir la comanda de los productos del pedido.
            @return: bool
        """
        en_curso = self.comprobar_estado_en_curso()
        es_vendedor = usuario.esVendedor
        return en_curso and es_vendedor

    def comprobar_tipo_valido(self, tipo):
        """
            Devuelve true si el tipo es retiro o deliver.
            @param tipo: str
            @return: bool
        """
        valido = tipo == self.TIPO_RETIRO or tipo == self.TIPO_DELIVERY
        return valido

    def comprobar_tipo_delivery(self, tipo):
        """
            Devuelve true si el tipo es delivery.
            @param tipo: str
            @return: bool
        """
        return tipo == self.TIPO_DELIVERY

    def get_lineas_comanda(self):
        """
            Devuelve las líneas a imprimir en la comanda.
            @return: List
        """
        lineas = self.lineas.all()
        return lineas

    # Actualiza el total del pedido, según los precios y cantidades de las líneas.
    def actualizar_total(self):
        lineas = self.lineas.all()
        total = 0
        for linea in lineas:
            total += linea.total
        self.total = total
        self.save()

    # Agrega un estado al pedido.
    def agregar_estado(self, estado):
        ultimo = self.estados.order_by('-fecha').filter(estado=estado).first()
        anterior = ultimo.estado if ultimo is not None else ''
        if ultimo is None or anterior != estado:
            objeto = Estado(estado=estado, pedido=self)
            objeto.save()
            self.ultimo_estado = estado
            self.estados.add(objeto)
        else:
            ultimo.fecha = datetime.datetime.now()
            ultimo.save()

        ultimo = self.estados.order_by('-fecha').filter(estado=estado).first()
        ultimo_coleccion = ultimo.estado
        ultimo_estado = self.ultimo_estado
        if ultimo_estado != ultimo_coleccion:
            self.ultimo_estado = ultimo_coleccion
            self.save()

    # Borra todos los estados y líneas del pedido.
    def borrar_datos_pedido(self):
        self.estados.all().delete()
        self.lineas.all().delete()
        self.save()

    # Agrega al pedido un nuevo estado Entregado
    def entregar(self):
        self.agregar_estado(Estado.RECIBIDO)
        self.save()

    def crear_venta(self):
        """
            Crea una venta de tipo online.
            @return: None
        """
        usuario = self.usuario
        venta = Venta(usuario=usuario, tipo=Venta.ONLINE, pedido=self)
        venta.save()

        lineas = self.lineas.all()
        for linea in lineas:
            producto = linea.producto
            cantidad = linea.cantidad
            precio = producto.precio_vigente
            total = precio * cantidad
            linea = VentaLinea(venta=venta, producto=producto, cantidad=cantidad, precio=precio, total=total)
            linea.save()

        venta.actualizar()
        venta.save()
        self.venta = venta

    def get_tipo_texto(self):
        """
            Devuelve el tipo de pedido.
            @return:  str
        """
        tipo = self.tipo
        if tipo == self.TIPO_RETIRO:
            return "Retirar"
        if tipo == self.TIPO_DELIVERY:
            return "Delivery"

    # Devuelve el estado en formato legible.
    def get_estado_texto(self, logueado):
        estado = self.ultimo_estado.capitalize()
        recibido = self.comprobar_estado_recibido()
        le_pertenece = self.usuario_id == logueado.id
        if not le_pertenece and recibido:
            return Estado.ENTREGADO.capitalize()
        return estado

    # Devuelve la clase css del estado.
    def get_estado_clase(self):
        clase = "font-weight-bold"
        estado = self.ultimo_estado
        if estado == Estado.ANULADO:
            clase = clase + " text-danger"
        if estado == Estado.RECIBIDO:
            clase = clase + " text-success"
        if estado == Estado.ABIERTO or estado == Estado.EN_CURSO:
            return ""
        return clase

    # Devuelve el id legible del pedido.
    def get_id_texto(self):
        return "P" + str(self.id).zfill(5)

    def get_titulo_comanda(self):
        """
            Devuelve el título de la comanda.
            @return: str
        """
        id_texto = self.get_id_texto()
        titulo = 'Comanda Pedido ' + id_texto
        return titulo


class PedidoLinea(models.Model):
    pedido = models.ForeignKey('gastronomia.Pedido', on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey('producto.Producto', on_delete=models.PROTECT, related_name="+")
    cantidad = models.IntegerField()
    subtotal = models.FloatField()
    total = models.FloatField()

    # Actualiza el total de la línea según el precio vigente del producto.
    def actualizar_total(self):
        precio = self.producto.precio_vigente
        total = precio * self.cantidad
        self.subtotal = precio
        self.total = total
        self.save()

    def get_cantidad_comanda(self):
        """
            Devuelve la cantidad a preparar del cocinero para el producto de la línea actual.
            @return: int
        """
        return self.cantidad


class Venta(Auditoria, models.Model):

    ALMACEN = 'almacen'
    ONLINE = 'online'
    MESA = 'mesa'

    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="ventas")
    pedido = models.ForeignKey('gastronomia.Pedido', null=True, on_delete=models.CASCADE, related_name="+")
    turno = models.ForeignKey('mesas.Turno', null=True, on_delete=models.CASCADE, related_name="+")
    total = models.FloatField(default=0)
    tipo = models.CharField(max_length=30, default=ALMACEN)
    anulado = models.DateTimeField(null=True)

    def actualizar(self):
        self.actualizar_lineas()
        self.actualizar_total()

    def actualizar_lineas(self):
        lineas = self.lineas.all()
        for linea in lineas:
            linea.actualizar()

    # Actualiza el total de la venta a partir del total de cada línea.
    def actualizar_total(self):
        lineas = self.lineas.all()
        total = 0
        for linea in lineas:
            total += linea.total
        self.total = total
        self.save()

    # Crea un movimiento de stock por cada producto vendido.
    def crear_movimientos(self):
        lineas = self.lineas.all()
        for linea in lineas:
            linea.crear_movimiento()

    # Devuelve true si el usuario puede visualizar el ingreso.
    def comprobar_puede_visualizar(self, usuario):
        es_admin = usuario.esAdmin
        es_vendedor = usuario.esVendedor
        return es_admin or es_vendedor

    # Devuelve true si el usuario puede anular la venta.
    def comprobar_puede_anular(self, usuario):
        es_admin = usuario.esAdmin
        es_vendedor = usuario.esVendedor
        anulado = self.comprobar_anulada()
        tipo = self.tipo
        return (es_admin or es_vendedor) and not anulado and tipo == self.ALMACEN

    # Devuelve true si la venta no está anulada.
    def comprobar_anulada(self):
        anulado = self.anulado
        return anulado is not None

    def comprobar_puede_emitir_comanda(self):
        """
            Devuelve true si puede emitar la comanda.
            @return: bool
        """
        tipo = self.tipo
        return tipo == self.ALMACEN or tipo == self.ONLINE

    # Anula la venta generando un movimiento de stock a los productos ingresados.
    def anular(self):
        self.anulado = datetime.datetime.now()
        lineas = self.lineas.all()
        for linea in lineas:
            linea.anular()

    # Devuelve la clase del estado de la venta.
    def get_estado_clase(self):
        clase = 'font-weight-bold'
        anulado = self.comprobar_anulada()
        if anulado:
            clase += ' text-danger'
        else:
            clase += ' text-success'
        return clase

    # Devuelve la fecha de anulación de la venta. En caso que no haya sido anulada devuelve string vacío.
    def get_fecha_anulada_texto(self):
        anulado = self.anulado
        if anulado is None:
            return ""
        return anulado.strftime('%d/%m/%Y %H:%M')

    # Devuelve el estado de la venta. Puede ser activa o anulado.
    def get_estado_legible(self):
        anulado = self.comprobar_anulada()
        if anulado:
            return 'Anulada'
        return 'Activa'

    # Devuelve el id legible de la venta.
    def get_id_texto(self):
        return "V" + str(self.id).zfill(5)

    def get_id_texto_limpio(self):
        """
            Devuelve el id llenandolo con ceros.
            @return: str
        """
        return str(self.id).zfill(5)

    def get_tipo_texto(self):
        """
            Devuelve el tipo de venta legible.
            @return: str
        """
        tipo = self.tipo
        if tipo == self.ALMACEN:
            return "Almacén"

        if tipo == self.MESA:
            return "Mesa"

        if tipo == self.ONLINE:
            return "Online"

        return ""

    def comprobar_tipo_online(self):
        """
            Devuelve true si es una venta tipo online.
            @return: bool
        """
        tipo = self.tipo
        return tipo == self.ONLINE

    def get_tipo_online_texto(self):
        """
            Devuelve el tipo de pedido online que se realizó.
            @return: str
        """
        online = self.comprobar_tipo_online()
        if not online:
            return ''

        pedido = self.pedido
        if pedido is None:
            return ""

        tipo = pedido.tipo
        if tipo == Pedido.TIPO_RETIRO:
            return 'Retiro'
        if tipo == Pedido.TIPO_DELIVERY:
            return 'Delivery'

        return ''


    def get_vuelto_texto(self):
        """
            Calcula y devuelve el vuelto según el cambio ingresado del usuario.
            @return: str
        """
        pedido = self.pedido
        if pedido is None:
            return ''

        cambio = pedido.cambio
        if cambio <= 0:
            return 'no solicitó'

        total = self.total
        vuelto = cambio - total
        if vuelto < 0:
            return 'no solicitó'
        return "$ " + str(vuelto)

    def get_direccion_texto(self):
        """
            Si la venta se generó de un pedido por delivery devuelve la dirección.
            @return: str
        """
        pedido = self.pedido
        if pedido is None:
            return ''

        tipo = pedido.tipo
        tipo_delivery = pedido.comprobar_tipo_delivery(tipo)
        if not tipo_delivery:
            return ''

        direccion = pedido.direccion
        if len(direccion) > 0:
            return direccion

        return ''

    def get_nombre(self):
        """
            Devuelve el nombre de la venta. Ej: Venta V00001
            @return: str
        """
        id_texto = self.get_id_texto()
        return "Venta " + id_texto

    def get_titulo_comanda(self):
        """
            Devuelve el título de la comanda.
            @return: str
        """
        id_texto = self.get_id_texto()
        titulo = 'Comanda Venta ' + id_texto
        return titulo

    def get_lineas_comanda(self):
        """
            Devuelve las líneas a imprimir en la comanda.
            @return: List
        """
        lineas = self.lineas.all()
        return lineas

    def __str__(self):
        id_texto = self.get_id_texto()
        return "Venta " + id_texto


class VentaLinea(models.Model):
    venta = models.ForeignKey('gastronomia.Venta', on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey('producto.Producto', on_delete=models.PROTECT, related_name="+")
    cantidad = models.IntegerField()
    precio = models.IntegerField()
    total = models.FloatField(default=0)

    # Crea un movimiento de stock a partir del producto vendido.
    def crear_movimiento(self):
        producto = self.producto
        cantidad = self.cantidad
        descripcion = self.venta.__str__()

        producto.actualizar_stock(nueva=cantidad, descripcion=descripcion)
        producto.save()

    def actualizar(self):
        self.actualizar_total()

    # Actualiza el total de la línea a partir de la cantidad y el precio.
    def actualizar_total(self):
        precio = self.precio
        total = precio * self.cantidad
        self.total = total
        self.save()

    # Crea un nuevo movimiento de stock negativo y actualiza el stock del producto.
    def anular(self):
        cantidad = self.cantidad
        producto = self.producto
        anterior = producto.stock
        nueva = anterior - cantidad

        descripcion = self.venta.__str__() + " anulada"
        producto.actualizar_stock(nueva=nueva, descripcion=descripcion, venta_linea=self)
        producto.save()

    def get_cantidad_comanda(self):
        """
            Devuelve la cantidad a preparar del cocinero para el producto de la línea actual.
            @return: int
        """
        return self.cantidad

    def __str__(self):
        return "Línea de " + self.venta.__str__()
