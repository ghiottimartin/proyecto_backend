from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.backends import ModelBackend


class EmailBackend(ModelBackend):

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(email=username)
        except UserModel.DoesNotExist:
            return None

        valida = user.check_password(password)
        if valida is False:
            raise ValidationError("Usuario y/o contraseña incorrectos.")
        habilitado = user.habilitado
        if valida and habilitado is False:
            raise ValidationError("Su usuario no ha sido habilitado aún. Revise su correo para activarlo.")
        return user
