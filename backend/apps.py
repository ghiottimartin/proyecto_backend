from django.apps import AppConfig
from django.db.models.signals import post_save
from . import signals


class BackendConfig(AppConfig):
    name = 'backend'

    def ready(self):

        # registering signals with the model's string label
        post_save.connect(signals.agregar_auditorias, sender='backend.Usuario')
