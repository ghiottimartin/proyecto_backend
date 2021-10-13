from base.respuestas import Respuesta
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response

respuesta = Respuesta()


class CustomAuthToken(ObtainAuthToken):

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        if user.borrado:
            return respuesta.get_respuesta(False, "El usuario ha sido borrado, contacte un administrador")
        return Response({
            'token': token.key,
            'idUsuario': user.pk,
            'nombre': user.first_name
        })
