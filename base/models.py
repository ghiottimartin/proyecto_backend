from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
import datetime


class Auditoria(models.Model):
    auditoria_creado_fecha = models.DateTimeField(default=datetime.datetime.now, blank=True)
    auditoria_modificado_fecha = models.DateTimeField(default=datetime.datetime.now, blank=True)

    auditoria_creador = models.ForeignKey('base.Usuario', on_delete=models.CASCADE, related_name="+", null=True)
    auditoria_modificado = models.ForeignKey('base.Usuario', on_delete=models.CASCADE, related_name="+", null=True)

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
        else:
            raise ValidationError({"Error": "No se ha podido crear el usuario con rol comensal."})

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


# Busca el rol por nombre.
def get_rol(rol):
    try:
        return Rol.objects.get(nombre=rol)
    except Rol.DoesNotExist:
        return None
