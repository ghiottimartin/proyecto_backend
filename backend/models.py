from django.core.exceptions import ValidationError
from django.contrib.auth.models import AbstractUser
from django.db import models


class Usuario(AbstractUser):
    username = models.CharField(unique=False, max_length=50)
    email = models.EmailField(unique=True)
    token_reset = models.CharField(max_length=191, null=True)
    token_email = models.CharField(max_length=191, null=True)
    fecha_token_reset = models.DateTimeField(null=True)

    roles = models.ManyToManyField(
        to='Rol', related_name="usuarios_roles", blank=True)

    def agregar_rol(self, rol):
        exists = self.roles.filter(id=rol.id).first()
        if not exists:
            self.roles.add(rol)

    def agregar_roles(self, roles):
        for rol in roles:
            objetoRol = get_rol(rol)
            if objetoRol is None:
                raise ValidationError({"Error": "No se ha encontrado el rol."})
            self.agregar_rol(objetoRol)


class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    legible = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=250)
    root = models.BooleanField(default=False)

    ROOT = 'root'
    MOZO = 'mozo'
    COMENSAL = 'comensal'
    VENEDEDOR = 'vendedor'
    ADMINISTRADOR = 'administrador'

    ROLES = (ROOT, MOZO, COMENSAL, VENEDEDOR, ADMINISTRADOR)


class Producto(models.Model):
    nombre = models.CharField(max_length=30)
    precio = models.FloatField()

    def __str__(self):
        return self.nombre


def get_rol(rol):
    if rol is None:
        rol = Rol.COMENSAL
    try:
        return Rol.objects.get(nombre=rol)
    except Rol.DoesNotExist:
        return None
