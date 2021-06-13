from django.apps import AppConfig
from django.db.models.signals import pre_save, pre_delete
from backend.signals import agregar_auditorias, borrar_imagen


class ProductoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'producto'

    # registering signals with the model's string label
    pre_save.connect(agregar_auditorias, sender='producto.Categoria')
    pre_save.connect(agregar_auditorias, sender='producto.Producto')
    pre_delete.connect(borrar_imagen, sender='producto.Producto')

