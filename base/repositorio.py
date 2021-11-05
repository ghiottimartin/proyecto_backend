from .models import Usuario, Rol


def get_usuario(pk, rol=None):
    """
        Busca un usuario por id.
        @param pk: Id del usuario
        @param rol: Rol del usuario
        @return: Usuario|None
    """
    try:
        filtros = {}
        if isinstance(pk, int):
            filtros["id"] = pk
        if isinstance(rol, str):
            filtros["roles__nombre__contains"] = rol
        return Usuario.objects.get(**filtros)
    except Usuario.DoesNotExist:
        return None


def buscar_mozos(mozos):
    """
        Busca los mozos por id.
        @param mozos: Mozos.
        @return: List
    """
    buscados = []
    try:
        for mozo in mozos:
            id = mozo["id"]
            buscado = get_usuario(id, Rol.MOZO)
            if isinstance(buscado, Usuario):
                buscados.append(buscado)
    except Exception:
        return []
    return buscados
