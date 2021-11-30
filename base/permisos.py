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


class TieneRolMozo(permissions.BasePermission):
    message = 'No tiene rol de mozo para realizar esta acción.'

    def has_permission(self, request, view):
        return tiene_rol(request, Rol.MOZO)


class TieneRolAdminOMozo(permissions.BasePermission):
    message = 'No tiene rol de mozo o administrador para realizar esta acción.'

    def has_permission(self, request, view):
        mozo = tiene_rol(request, Rol.MOZO)
        admin = tiene_rol(request, Rol.ADMINISTRADOR)
        return mozo or admin


class TieneRolAdminOVendedor(permissions.BasePermission):
    message = 'No tiene rol de vendedor o administrador para realizar esta acción.'

    def has_permission(self, request, view):
        vendedor = tiene_rol(request, Rol.VENEDEDOR)
        admin = tiene_rol(request, Rol.ADMINISTRADOR)
        return vendedor or admin
