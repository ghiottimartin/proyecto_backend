from django.db import models
from base.models import Auditoria, Usuario
import datetime


class Estado(models.Model):
    pedido = models.ForeignKey('gastronomia.Pedido', on_delete=models.CASCADE, related_name="estados")
    estado = models.CharField(max_length=40)
    fecha = models.DateTimeField(default=datetime.datetime.now)

    ABIERTO = 'abierto'
    CERRADO = 'cerrado'
    RECIBIDO = 'recibido'
    CANCELADO = 'cancelado'
    ENTREGADO = 'entregado'

    @classmethod
    def comprobar_estado_valido(cls, estado):
        return estado == cls.ABIERTO or estado == cls.CERRADO


class Pedido(Auditoria, models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="+")
    fecha = models.DateTimeField(default=datetime.datetime.now)
    ultimo_estado = models.CharField(max_length=40, default=Estado.ABIERTO)
    total = models.FloatField()
    forzar = models.BooleanField(default=False)
    tipo = models.CharField(max_length=15)

    TIPO_ONLINE = 'online'
    TIPO_MOSTRADOR = 'mostrador'

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

    def comprobar_estado_recibido(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.RECIBIDO

    def comprobar_estado_cancelado(self):
        ultimo_estado = self.ultimo_estado
        return ultimo_estado == Estado.CANCELADO

    def comprobar_puede_visualizar(self, usuario):
        es_admin = usuario.esAdmin
        es_vendedor = usuario.esVendedor
        pedido_usuario = self.usuario
        le_pertenece = pedido_usuario == usuario
        return le_pertenece or es_admin or es_vendedor

    def comprobar_puede_cerrar(self, usuario):
        cerrado = self.comprobar_estado_cerrado()
        es_vendedor = usuario.esVendedor
        return cerrado and es_vendedor

    def comprobar_puede_cancelar(self, usuario):
        abierto = self.comprobar_estado_abierto()
        es_vendedor = usuario.esVendedor
        pedido_usuario = self.usuario
        le_pertenece = pedido_usuario == usuario
        return (es_vendedor or le_pertenece) and abierto

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

    def recibir_pedido(self):
        self.agregar_estado(Estado.RECIBIDO)
        self.save()

    def get_estado_texto(self, logueado):
        estado = self.ultimo_estado.capitalize()
        recibido = self.comprobar_estado_recibido()
        le_pertenece = self.usuario_id == logueado.id
        if not le_pertenece and recibido:
            return Estado.ENTREGADO.capitalize()
        return estado

    def get_estado_clase(self):
        clase = "font-weight-bold"
        estado = self.ultimo_estado
        if estado == Estado.CANCELADO:
            clase = clase + " text-danger"
        if estado == Estado.RECIBIDO:
            clase = clase + " text-success"
        if estado == Estado.ABIERTO or estado == Estado.CERRADO:
            return ""
        return clase


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



