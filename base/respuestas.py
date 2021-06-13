from rest_framework.response import Response
from rest_framework import status


# Devuelve una respuesta lista para ser recibida por el frontend. Indicando un valor booleano en la clave 'exito' y un
# mensaje en la clave 'message'. Dependiendo del éxito devuelve el código HTTP correspondiente pudiendo indicar uno
# personalizado por el parámetro 'codigo'. Si deseamos devolver datos podemos hacerlo mediante el parámetro 'datos'.
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
    if isinstance(datos, list):
        indice = 0
        while indice < len(datos):
            error = datos[indice]
            indice += 1
            respuesta.update({"datos": error})
    return Response(respuesta, status=codigo)


# Respuesta exitosa por defecto sin mensaje ni datos.
def exito():
    return get_respuesta(True)


# # Respuestas de la acción validar token
def validar_token_email_error_token_invalido():
    mensaje = "El token ingresado no es válido o ha caducado. Comuníquese con nosotros mediante la sección."
    return get_respuesta(False, mensaje)


def validar_token_email_error_general():
    mensaje = "Hubo un error al activar su cuenta. Intente de nuevo más tarde."
    return get_respuesta(False, mensaje)


# # Respuestas de la acción olvido contraseña.
def olvido_password_error_email_inexistente():
    mensaje = "El email ingresado no corresponde a ningún usuario registrado."
    return get_respuesta(False, mensaje)


def olvido_password_error_general():
    mensaje = "Hubo un error al enviar el email de cambio de contraseña. Intente nuevamente más tarde."
    return get_respuesta(False, mensaje)


def olvido_password_exito():
    mensaje = "Se ha enviado un link a su email para reiniciar su contraseña. Tiene 24 horas para cambiarla."
    return get_respuesta(True, mensaje)


# # Respuestas de la acción validar token de cambio de contraseña.
def validar_token_password_error_general():
    mensaje = "Hubo un error intentar validar el link. Intente de nuevo más tarde."
    return get_respuesta(False, mensaje)


def validar_token_password_error_link_invalido():
    mensaje = "El link ingresado no es válido o ha caducado. Vuelva a solicitar el cambio de contraseña."
    return get_respuesta(False, mensaje)


# # Respuestas de la acción cambiar contraseña.
def cambiar_password_error_general():
    mensaje = "Hubo un error cambiar la contraseña. Intente de nuevo más tarde."
    return get_respuesta(False, mensaje)


def cambiar_password_exito():
    mensaje = "La contraseña fue cambiada con éxito, intente ingresar nuevamente."
    return get_respuesta(True, mensaje)
