from rest_framework import permissions
from base.models import Usuario, Rol


class TieneRolAdmin(permissions.BasePermission):
    message = 'No tiene rol de administrador para realizar esta acción.'

    def has_permission(self, request, view):
        usuario = request.user
        habilitado = False
        if isinstance(usuario, Usuario):
            habilitado = usuario.comprobar_tiene_rol(Rol.ADMINISTRADOR)
        return habilitado
