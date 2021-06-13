from django.apps import AppConfig
from django.db.models.signals import pre_save
from . import signals


class BaseConfig(AppConfig):
    name = 'base'

    def ready(self):

        # registering signals with the model's string label
        pre_save.connect(signals.agregar_auditorias, sender='base.Usuario')
