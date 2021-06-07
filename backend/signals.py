def agregar_auditorias(sender, instance, created, **kargs):
    if created:
        agregar_auditoria_creado(instance)
    else:
        agregar_auditoria_actualizado(instance)


def agregar_auditoria_creado(entidad):
    print('creado')
    pass


def agregar_auditoria_actualizado(entidad):
    print('actualizado')
    pass
