from django.apps import AppConfig
from django.db.models.signals import pre_save
from base.signals import agregar_auditorias


class MesasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'mesas'

    # registering signals with the model's string label
    pre_save.connect(agregar_auditorias, sender='mesas.Mesa')
    pre_save.connect(agregar_auditorias, sender='mesas.Turno')