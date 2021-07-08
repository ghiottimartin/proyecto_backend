from .models import Pedido, PedidoLinea, Estado
from producto.models import get_producto
from django.core.exceptions import ValidationError


# Devuelve un pedido por estado.
def get_pedido(pk=None, usuario=None, estado=None):
    try:
        if pk is not None:
            return Pedido.objects.get(pk=pk)
        if usuario is not None and estado is not None:
            return Pedido.objects.get(ultimo_estado=estado, usuario=usuario)
    except Pedido.DoesNotExist:
        return None


# Valida que los datos del pedido sean correctos.
def validar_crear_pedido(datos):
    if not isinstance(int(datos["id"]), int) or int(datos["id"] < 0):
        raise ValidationError("El pedido no tiene los datos suficientes para ser guardado.")
    lineas = datos["lineas"] if "lineas" in datos else list()
    if not isinstance(lineas, list):
        raise ValidationError("Debe seleccionar al menos un producto.")
    else:
        for linea in lineas:
            id_producto = linea["producto"] if "producto" in linea else 0
            if id_producto <= 0:
                raise ValidationError("No se ha encontrado el producto.")
            cantidad = linea["cantidad"] if "cantidad" in linea else 0
            if cantidad <= 0:
                raise ValidationError("La cantidad del producto debe ser mayor a cero.")


def crear_pedido(usuario, lineas):
    pedido = Pedido(usuario=usuario, ultimo_estado=Estado.ABIERTO, total=0)
    for item in lineas:
        linea = crear_linea_pedido(pedido, item)
        linea.save()
    return pedido


def crear_linea_pedido(pedido, item):
    producto = get_producto(item["producto"])
    if producto is None:
        raise Exception("No se ha encontrado el producto.")
    cantidad = item["cantidad"]
    linea = PedidoLinea(pedido=pedido, producto=producto, cantidad=cantidad)
    return linea


def actualizar_pedido(id, lineas):
    pedido = get_pedido(pk=id)
    if pedido is None:
        raise ValidationError("No se ha encontrado el pedido.")
    actualizar_lineas_pedido(pedido, lineas)
    return pedido


def actualizar_lineas_pedido(pedido, lineas):
    for linea in lineas:
        id = linea["id"]
        if id > 0:
            objeto = get_linea_pedido(id)
        else:
            objeto = crear_linea_pedido(pedido, linea)
        if objeto is None:
            raise ValidationError("No se ha encontrado al línea del pedido de id " + id)
        if id > 0:
            objeto.cantidad = linea["cantidad"]
        objeto.save()


def get_linea_pedido(id):
    try:
        if id is not None:
            return PedidoLinea.objects.get(pk=id)
    except Pedido.DoesNotExist:
        return None
