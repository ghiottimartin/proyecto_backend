from django.db import models
from django.utils.translation import gettext_lazy as _
from base.models import Auditoria
from utils import get_ruta_nombre_archivo


class Categoria(Auditoria, models.Model):
    superior = models.ForeignKey(
        'Categoria', on_delete=models.PROTECT, related_name="inferiores", null=True, blank=True)
    nombre = models.CharField(max_length=30)
    habilitado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class Producto(Auditoria, models.Model):
    categoria = models.ForeignKey(
        Categoria, on_delete=models.PROTECT, related_name="productos", default="productos")
    nombre = models.CharField(max_length=50)
    imagen = models.ImageField(_("Image"), upload_to=get_ruta_nombre_archivo, null=True, default="producto/defecto"
                                                                                                 "/default.jpg")
    imagen_nombre = models.CharField(max_length=50, default="default.jpg")
    descripcion = models.CharField(max_length=255, default="")
    precio_vigente = models.FloatField(default=0.00)
    habilitado = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre