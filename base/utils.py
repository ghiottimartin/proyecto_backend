from datetime import datetime, time


def get_fecha_string2objeto(fechaTexto, inicioDelDia=True):
    date_str = fechaTexto

    date_obj = datetime.strptime(date_str, '%Y-%m-%d')

    hora = time.max
    if inicioDelDia:
        hora = time.min

    date_time_obj = datetime.combine(date_obj, hora)
    return date_time_obj
