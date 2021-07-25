import datetime
from jumbo_soft.middleware import get_request


def get_usuario_logueado():
    usuario = None if get_request() is None else get_request().user
    logueado = None if usuario is None or usuario.id is None else usuario
    return logueado


def agregar_auditorias(sender, instance, **kwargs):
    logueado = get_usuario_logueado()
    if instance.id is None:
        agregar_auditoria_creado(instance, logueado)
    else:
        agregar_auditoria_actualizado(instance, logueado)


def agregar_auditoria_creado(entidad, logueado):
    entidad.auditoria_creador = logueado
    entidad.auditoria_modificado = logueado
    entidad.auditoria_modificado_fecha = datetime.datetime.now()
    entidad.auditoria_creado_fecha = datetime.datetime.now()


def agregar_auditoria_actualizado(entidad, logueado):
    entidad.auditoria_modificado = logueado
    entidad.auditoria_modificado_fecha = datetime.datetime.now()
