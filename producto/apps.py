from django.apps import AppConfig
from django.db.models.signals import pre_save
from base.signals import agregar_auditorias


class ProductoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'producto'

    # registering signals with the model's string label
    pre_save.connect(agregar_auditorias, sender='producto.Categoria')
    pre_save.connect(agregar_auditorias, sender='producto.Producto')
    pre_save.connect(agregar_auditorias, sender='producto.Ingreso')
    pre_save.connect(agregar_auditorias, sender='producto.MovimientoStock')
    pre_save.connect(agregar_auditorias, sender='producto.Precio')
    pre_save.connect(agregar_auditorias, sender='producto.Costo')
    pre_save.connect(agregar_auditorias, sender='producto.ReemplazoMercaderia')

