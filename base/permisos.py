from rest_framework import permissions


class TieneRolAdmin(permissions.BasePermission):
    message = 'No tiene permiso para realizar esta acción.'

    def has_permission(self, request, view):
        usuario = request.user
        return usuario and usuario.esAdmin
