from django.db import models
from backend.models import Auditoria


class Categoria(Auditoria, models.Model):
    superior = models.ForeignKey(
        'Categoria', on_delete=models.PROTECT, related_name="inferiores", null=True, blank=True)
    nombre = models.CharField(max_length=30)
    habilitado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Producto(Auditoria, models.Model):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos")
    nombre = models.CharField(max_length=50)
    imagen = models.ImageField(upload_to='images/', null=True)
    descripcion = models.CharField(max_length=255, default="")
    precio_vigente = models.FloatField(default=0.00)
    habilitado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre
