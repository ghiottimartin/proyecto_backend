import datetime
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class Auditoria(models.Model):
    auditoria_creado_fecha = models.DateTimeField(default=datetime.datetime.now, blank=True)
    auditoria_modificado_fecha = models.DateTimeField(default=datetime.datetime.now, blank=True)

    auditoria_creador = models.ForeignKey('jumbo_soft.Usuario', on_delete=models.CASCADE, related_name="+", null=True)
    auditoria_modificado = models.ForeignKey('jumbo_soft.Usuario', on_delete=models.CASCADE, related_name="+", null=True)

    class Meta:
        abstract = True


class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    legible = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=250)
    root = models.BooleanField(default=False)

    ROOT = 'root'
    MOZO = 'mozo'
    COMENSAL = 'comensal'
    VENEDEDOR = 'vendedor'
    ADMINISTRADOR = 'admin'

    ROLES = (ROOT, MOZO, COMENSAL, VENEDEDOR, ADMINISTRADOR)


class Usuario(Auditoria, AbstractUser):
    roles = models.ManyToManyField(
        to='Rol', related_name="usuarios_roles", blank=True)
    dni = models.PositiveIntegerField(
        validators=[MinValueValidator(1000000), MaxValueValidator(99999999)],
        null=True,
        unique=True
    )
    email = models.EmailField(unique=True)
    username = models.CharField(unique=False, max_length=50)
    password = models.CharField(max_length=128, null=True)
    habilitado = models.BooleanField(default=False)
    token_reset = models.TextField(null=True)
    token_email = models.TextField(null=True)
    fecha_token_reset = models.DateTimeField(null=True)
    operaciones = list()
    borrado = models.BooleanField(default=False)

    esMozo = False
    esAdmin = False
    esComensal = False
    esVendedor = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id is not None:
            self.esMozo = self.comprobar_tiene_rol(Rol.MOZO)
            self.esAdmin = self.comprobar_tiene_rol(Rol.ADMINISTRADOR)
            self.esComensal = self.comprobar_tiene_rol(Rol.COMENSAL)
            self.esVendedor = self.comprobar_tiene_rol(Rol.VENEDEDOR)
            self.operaciones = self.get_operaciones()

    # Agrega el rol comensa al usuario.
    def agregar_rol_comensal(self):
        comensal = get_rol(Rol.COMENSAL)
        if isinstance(comensal, Rol):
            self.agregar_rol(comensal)
            return ""
        else:
            return "No se ha podido agregar el rol " + Rol.COMENSAL

    # Agrega un rol al usuario, el parámetro rol puede ser el id del rol, un objeto Rol o el nombre rol.
    def agregar_rol(self, rol):
        # Defino el parámetro para buscar el rol.
        id = rol
        if isinstance(id, Rol):
            id = rol.id
        filtro = {'id': id}
        if isinstance(rol, str):
            filtro = {'nombre': rol}
        existe = self.roles.filter(**filtro).first()

        # Si no tiene el rol se lo agrego.
        objeto = rol
        if isinstance(objeto, str):
            objeto = Rol.objects.get(nombre=rol)
        if not existe and isinstance(objeto, Rol):
            self.roles.add(objeto)

    # Si tiene el rol a quitar, se lo remueve de la colección de roles.
    def quitar_rol(self, rol):
        existe = self.roles.filter(nombre=rol).first()
        if existe:
            self.roles.remove(existe)

    # Según los cambios en los campos esMozo, esComensal y esVendedor se actualiza los roles del usuario.
    def actualizar_roles(self, usuario):
        self.actualizar_rol(usuario, Rol.MOZO)
        self.actualizar_rol(usuario, Rol.COMENSAL)
        self.actualizar_rol(usuario, Rol.VENEDEDOR)

    # Quita o agrega el rol al usuario dependiendo de los campos es'NombreRol'.
    def actualizar_rol(self, usuario, rol):
        buscar = "es" + rol.capitalize()
        agregarRol = usuario.get(buscar)
        tieneRol = self.comprobar_tiene_rol(rol)

        # Si es'NombreRol' es verdadero y no tenía el rol anteriormente le agregamos el rol.
        if agregarRol and tieneRol is False:
            self.agregar_rol(rol)
        # Si es'NombreRol' es falso y tenía el rol anteriormente le quitamos el rol.
        elif agregarRol is False and tieneRol:
            self.quitar_rol(rol)

    # Comprueba si el usuario tiene el rol a partir del nombre del mismo.
    def comprobar_tiene_rol(self, nombre):
        existe = self.roles.filter(nombre=nombre).first()
        return isinstance(existe, Rol)

    # Devuelve las operaciones del usuario según los roles del mismo.
    def get_operaciones(self):
        operaciones_admin = self.get_operaciones_admin()
        return operaciones_admin

    # Devuele las operaciones para el rol administrador si tiene el rol indicado.
    def get_operaciones_admin(self):
        # Si no lo tiene devolvemos un diccionario vacío.
        if self.esAdmin is not True:
            return dict()

        operaciones = [{
            "rol": Rol.ADMINISTRADOR,
            "ruta": "/productos/listar/admin",
            "titulo": "Productos",
            "descripcion": "Permite gestionar los productos del sistema"
        }, {
            "rol": Rol.ADMINISTRADOR,
            "ruta": "/usuarios/listar",
            "titulo": "Usuarios",
            "descripcion": "Permite gestionar los usuarios del sistema"
        }, {
            "rol": Rol.ADMINISTRADOR,
            "ruta": "/compras",
            "titulo": "Ingreso",
            "descripcion": "Permite ingresar mercadería"
        }]
        return operaciones

    def __str__(self):
        return self.username


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

    def __str__(self):
        return self.nombre


class Estado(models.Model):
    pedido = models.ForeignKey('jumbo_soft.Pedido', on_delete=models.CASCADE, related_name="estados")
    estado = models.CharField(max_length=40)
    fecha = models.DateTimeField(default=datetime.datetime.now)

    ABIERTO = 'abierto'
    CERRADO = 'cerrado'
    RECIBIDO = 'recibido'
    CANCELADO = 'cancelado'

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

    def comprobar_puede_entregar(self, usuario):
        cerrado = self.comprobar_estado_cerrado()
        es_admin = usuario.esAdmin
        es_vendedor = usuario.esVendedor
        return cerrado and (es_vendedor or es_admin)

    def comprobar_puede_cancelar(self, usuario):
        abierto = self.comprobar_estado_abierto()
        cerrado = self.comprobar_estado_cerrado()
        es_vendedor = usuario.esVendedor
        pedido_usuario = self.usuario
        le_pertenece = pedido_usuario == usuario
        return (abierto and le_pertenece) or (cerrado and es_vendedor)

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


class PedidoLinea(models.Model):
    pedido = models.ForeignKey('jumbo_soft.Pedido', on_delete=models.CASCADE, related_name="lineas")
    producto = models.ForeignKey('jumbo_soft.Producto', on_delete=models.PROTECT, related_name="+")
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


# Busca un producto por id.
def get_producto(pk):
    try:
        return Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return None


# Busca el rol por nombre.
def get_rol(rol):
    try:
        return Rol.objects.get(nombre=rol)
    except Rol.DoesNotExist:
        return None

