def agregar_auditorias(sender, instance, created, **kargs):
    if created:
        agregar_auditoria_creado(instance)
    else:
        agregar_auditoria_actualizado(instance)


def agregar_auditoria_creado(usuario):
    print('creado')
    pass


def agregar_auditoria_actualizado(usuario):
    print('actualizado')
    pass
