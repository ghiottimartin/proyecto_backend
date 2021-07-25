from django.apps import AppConfig
from django.db.models.signals import pre_save
from . import signals


class JumboSoftConfig(AppConfig):
    name = 'jumbo_soft'

    def ready(self):

        # Agrego auditoría a los usuarios
        pre_save.connect(signals.agregar_auditorias, sender='jumbo_soft.Usuario')
        pre_save.connect(signals.agregar_auditorias, sender='jumbo_soft.Categoria')
        pre_save.connect(signals.agregar_auditorias, sender='jumbo_soft.Producto')
