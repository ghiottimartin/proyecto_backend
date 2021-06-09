from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError


class EmailBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        es_ruta_admin = True if request.path == '/admin/login/' else False
        UserModel = get_user_model()
        try:
            filtro = {'email': username}
            if es_ruta_admin:
                filtro = {'username': username}
            user = UserModel.objects.get(**filtro)
        except UserModel.DoesNotExist:
            return None

        valida = user.check_password(password)
        if valida is False:
            raise ValidationError({"exito": False, "message": "Usuario y/o contraseña incorrectos."})
        habilitado = user.habilitado
        if valida and habilitado is False and es_ruta_admin is False:
            raise ValidationError({"exito": False, "message": "Su usuario no ha sido habilitado aún. Revise su correo "
                                                              "para activarlo."})
        if (es_ruta_admin and valida and user.is_staff) or (es_ruta_admin is False and valida):
            return user
