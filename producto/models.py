from django.db import models
from django.utils.translation import gettext_lazy as _
from base.models import Auditoria
import uuid


class Categoria(Auditoria, models.Model):
    superior = models.ForeignKey(
        'Categoria', on_delete=models.PROTECT, related_name="inferiores", null=True, blank=True)
    nombre = models.CharField(max_length=30)
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

    def __str__(self):
        return self.nombre
