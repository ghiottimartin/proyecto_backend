from .models import Pedido, PedidoLinea, Estado
from producto import repositorioProducto
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
            id_producto = linea["producto_id"] if "producto_id" in linea else 0
            if id_producto <= 0:
                raise ValidationError("No se ha encontrado el producto.")
            cantidad = linea["cantidad"] if "cantidad" in linea else 0
            if cantidad <= 0:
                raise ValidationError("La cantidad del producto debe ser mayor a cero.")


def crear_pedido(usuario, id, lineas, lineasIds):
    pedido = Pedido(usuario=usuario, ultimo_estado=Estado.ABIERTO, total=0)
    if id > 0:
        pedido = get_pedido(pk=id)
    if pedido is None:
        raise ValidationError("No se ha encontrado el pedido.")
    # Borrar lineas anteriores
    pedido.save()
    for item in lineas:
        linea = crear_linea_pedido(pedido, item)
        linea.save()
    return pedido


def crear_linea_pedido(pedido, item):
    producto = repositorioProducto.get_producto(item["producto_id"])
    if producto is None:
        raise Exception("No se ha encontrado el producto.")
    cantidad = item["cantidad"]
    linea = PedidoLinea(pedido=pedido, producto=producto, cantidad=cantidad)
    return linea