from rest_framework.response import Response
from rest_framework import status


def get_respuesta(exito, mensaje="", codigo=None, datos=None):
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


def exito():
    return get_respuesta(True)


def validar_token_email_error_token_invalido():
    mensaje = "El token ingresado no es válido o ha caducado. Comuníquese con nosotros mediante la sección."
    return get_respuesta(False, mensaje)


def validar_token_email_error_general():
    mensaje = "Hubo un error al activar su cuenta. Intente de nuevo más tarde."
    return get_respuesta(False, mensaje)


def olvido_password_error_email_inexistente():
    mensaje = "El email ingresado no corresponde a ningún usuario registrado."
    return get_respuesta(False, mensaje)


def olvido_password_error_general():
    mensaje = "Hubo un error al enviar el email de cambio de contraseña. Intente nuevamente más tarde."
    return get_respuesta(False, mensaje)


def olvido_password_exito():
    mensaje = "Se ha enviado un link a su email para reiniciar su contraseña. Tiene 24 horas para cambiarla."
    return get_respuesta(True, mensaje)


def validar_token_password_error_general():
    mensaje = "Hubo un error intentar validar el link. Intente de nuevo más tarde."
    return get_respuesta(False, mensaje)


def validar_token_password_error_link_invalido():
    mensaje = "El link ingresado no es válido o ha caducado. Vuelva a solicitar el cambio de contraseña."
    return get_respuesta(False, mensaje)


def cambiar_password_error_general():
    mensaje = "Hubo un error cambiar la contraseña. Intente de nuevo más tarde."
    return get_respuesta(False, mensaje)


def cambiar_password_exito():
    mensaje = "La contraseña fue cambiada con éxito, intente ingresar nuevamente."
    return get_respuesta(True, mensaje)
