from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    token_reset = models.CharField(max_length=191, null=True)
    token_email = models.CharField(max_length=191, null=True)
    fecha_token_reset = models.DateTimeField(null=True)

    roles = models.ManyToManyField(
        to='Rol', related_name="usuarios_roles", blank=True)

class Rol(models.Model):
    nombre =  models.CharField(max_length=50)
    legible =  models.CharField(max_length=50)
    descripcion =  models.CharField(max_length=250)
    root = models.BooleanField(default=False)

class Producto(models.Model):
    nombre = models.CharField(max_length=30)
    precio = models.FloatField()

    def __str__(self):
        return self.nombre
