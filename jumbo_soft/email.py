from django.core.mail import EmailMultiAlternatives


def enviar_email_registro(usuario):
    url = "http://localhost:3000/validar-email/" + str(usuario.token_email)
    subject, from_email, to = 'Activación de cuenta', 'sistemadegestion@gmail.com', usuario.email
    text_content = '¡Bienvenido al Sistema Gastronómica!.'
    html_content = '<p>Para activar su cuenta tiene que ingresar al siguiente <a href=' + str(url) + '>link</a>.</p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()


def enviar_email_cambio_password(usuario):
    url = "http://localhost:3000/reset-password/" + str(usuario.token_reset)
    subject, from_email, to = 'Cambiar contraseña', 'sistemadegestion@gmail.com', usuario.email
    text_content = '¡Bienvenido al Sistema Gastronómica!.'
    html_content = '<p>Para cambiar su contraseña tiene que ingresar al siguiente <a href=' + str(url) + '>link</a>.</p>'
    msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
    msg.attach_alternative(html_content, "text/html")
    msg.send()
