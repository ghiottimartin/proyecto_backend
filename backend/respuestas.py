from rest_framework.response import Response
from rest_framework import status


def get_respuesta(exito, mensaje, codigo=None, datos=None):
    if exito and codigo is None:
        codigo = status.HTTP_200_OK
    if exito is False and codigo is None:
        codigo = status.HTTP_400_BAD_REQUEST
    respuesta = {
        "exito": exito,
        "message": mensaje
    }
    if isinstance(datos, dict):
        respuesta.update(datos)
    return Response(respuesta, status=codigo)


def validar_token_email_error_token_invalido():
    mensaje = "El token ingresado no es válido o ha caducado. Comuníquese con nosotros mediante la sección."
    return get_respuesta(False, mensaje)


def validar_token_email_error_general():
    mensaje = "Hubo un error al activar su cuenta. Intente de nuevo más tarde."
    return get_respuesta(False, mensaje)
