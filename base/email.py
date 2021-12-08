from base.serializers import UsuarioSerializer
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def enviar_email_registro(usuario):
    subject, from_email, to = 'Panadería Independencia - Activación de cuenta', 'sistemadegestion@gmail.com', usuario.email
    text_content = '¡Bienvenido al Sistema Gastronómico!.'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to, "martinghiotti2013@gmail.com"])
    html_body = render_to_string("registro.html", {'usuario': usuario})
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def enviar_email_cambio_password(usuario):
    subject, from_email, to = 'Panadería Independencia - Cambiar contraseña', 'sistemadegestion@gmail.com', usuario.email
    text_content = '¡Bienvenido al Sistema Gastronómica!.'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to, "martinghiotti2013@gmail.com"])
    html_body = render_to_string("cambio-clave.html", {'usuario': usuario})
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def enviar_email_pedido_cerrado(pedido, mensaje):
    usuario = pedido.usuario
    subject, from_email, to = 'Panadería Independencia - Pedido confirmado', 'sistemadegestion@gmail.com', usuario.email
    text_content = 'Pedido confirmado.'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to, "martinghiotti2013@gmail.com"])
    html_body = render_to_string("pedido-confirmado.html", {'pedido': pedido, 'usuario': usuario, 'mensaje': mensaje})
    msg.attach_alternative(html_body, "text/html")
    msg.send()


def enviar_email_pedido_anulado(pedido):
    usuario = pedido.usuario
    subject, from_email, to = 'Panadería Independencia - Pedido anulado', 'sistemadegestion@gmail.com', usuario.email
    text_content = 'Pedido anulado.'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to, "martinghiotti2013@gmail.com"])
    html_body = render_to_string("pedido-anulado.html", {'pedido': pedido, 'usuario': usuario})
    msg.attach_alternative(html_body, "text/html")
    msg.send()
