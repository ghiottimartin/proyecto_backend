from django.db import models
from base.models import Auditoria, Usuario
import datetime


class Estado(models.Model):
    pedido = models.ForeignKey('gastronomia.Pedido', on_delete=models.CASCADE, related_name="estados")
    estado = models.CharField(max_length=40)
    fecha = models.DateTimeField(default=datetime.datetime.now)

    ABIERTO = 'abierto'
    EN_CURSO = 'en curso'
    RECIBIDO = 'recibido'
    CANCELADO = 'cancelado'
    ENTREGADO = 'entregado'

    # Comprueba si el estado es válido
    @classmethod
    def comprobar_estado_valido(cls, estado):
        return estado == cls.ABIERTO or estado == cls.EN_CURSO or estado == cls.RECIBIDO or estado == cls.CANCELADO or estado == cls.ENTREGADO


class Pedido(Auditoria, models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="pedidos")
    fecha = models.DateTimeField(default=datetime.datetime.now)
    ultimo_estado = models.CharField(max_length=40, default=Estado.ABIERTO)
    total = models.FloatField()
    forzar = models.BooleanField(default=False)
    tipo = models.CharField(max_length=15)
    observaciones = models.CharField(max_length=255, default="")

    TIPO_ONLINE = 'online'
    TIPO_MOSTRADOR = 'mostrador'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.save()
        self.agregar_estado(Estado.ABIERTO)

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

    # Devuelve true si el estado del pedido es cancelado.
    def comprobar_estado_cancelado(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.CANCELADO

    # Devuelve true si el usuario actual puede visualizar el pedido.
    def comprobar_puede_visualizar(self, usuario):
        es_admin = usuario.esAdmin
        es_vendedor = usuario.esVendedor
        pedido_usuario = self.usuario
        le_pertenece = pedido_usuario == usuario
        return le_pertenece or es_admin or es_vendedor

    # Devuelve true si el usuario actual puede entregar el pedido.
    def comprobar_puede_entregar(self, usuario):
        en_curso = self.comprobar_estado_en_curso()
        es_vendedor = usuario.esVendedor
        return en_curso and es_vendedor

    # Devuelve true si el usuario actual puede cancelar el pedido.
    def comprobar_puede_cancelar(self, usuario):
        abierto = self.comprobar_estado_abierto()
        en_curso = self.comprobar_estado_en_curso()
        es_vendedor = usuario.esVendedor
        pedido_usuario = self.usuario
        le_pertenece = pedido_usuario == usuario
        return (en_curso and es_vendedor) or (le_pertenece and abierto)

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
        if ultimo is None:
            objeto = Estado(estado=estado, pedido=self)
            objeto.save()
            self.ultimo_estado = estado
            self.estados.add(objeto)

    # Borra todos los estados y líneas del pedido.
    def borrar_datos_pedido(self):
        self.estados.all().delete()
        self.lineas.all().delete()
        self.save()

    # Agrega al pedido un nuevo estado Entregado
    def entregar_pedido(self):
        self.agregar_estado(Estado.RECIBIDO)
        self.save()

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
        if estado == Estado.CANCELADO:
            clase = clase + " text-danger"
        if estado == Estado.RECIBIDO:
            clase = clase + " text-success"
        if estado == Estado.ABIERTO or estado == Estado.EN_CURSO:
            return ""
        return clase


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
