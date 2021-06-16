from rest_framework import permissions
from base.models import Usuario, Rol


# Indica si la persona logueada tiene el rol pasado como parámetro.
def tiene_rol(request, rol):
    usuario = request.user
    habilitado = False
    if isinstance(usuario, Usuario):
        habilitado = usuario.comprobar_tiene_rol(rol)
    return habilitado


class TieneRolAdmin(permissions.BasePermission):
    message = 'No tiene rol de administrador para realizar esta acción.'

    def has_permission(self, request, view):
        return tiene_rol(request, Rol.ADMINISTRADOR)


class TieneRolComensal(permissions.BasePermission):
    message = 'No tiene rol de comensal para realizar esta acción.'

    def has_permission(self, request, view):
        return tiene_rol(request, Rol.COMENSAL)
