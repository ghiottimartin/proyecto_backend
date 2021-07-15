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
            try:
                id_producto = linea["producto"]["id"]
            except:
                id_producto = 0
            if id_producto <= 0:
                raise ValidationError("No se ha encontrado el producto.")
            cantidad = int(linea["cantidad"]) if "cantidad" in linea else 0
            if not isinstance(cantidad, int):
                raise ValidationError("La cantidad del producto debe tener un valor numérico.")


def crear_pedido(usuario, lineas):
    pedido = get_pedido(usuario=usuario, estado=Estado.ABIERTO)
    if pedido is None:
        pedido = Pedido(usuario=usuario, ultimo_estado=Estado.ABIERTO, total=0)
        pedido.save()
    for item in lineas:
        crear_linea_pedido(pedido, item)
    vacio = pedido.comprobar_vacio()
    if vacio:
        pedido.borrar_datos_pedido()
        pedido.delete()
        return None
    pedido.actualizar_total()
    return pedido


def crear_linea_pedido(pedido, item):
    producto = get_producto(item["producto"]["id"])
    if producto is None:
        raise Exception("No se ha encontrado el producto.")
    cantidad = item["cantidad"]
    if int(cantidad) == 0:
        return None
    linea = PedidoLinea(pedido=pedido, producto=producto, cantidad=cantidad)
    linea.save()
    return linea


def actualizar_pedido(id, lineas):
    pedido = get_pedido(pk=id)
    if pedido is None:
        raise ValidationError("No se ha encontrado el pedido.")
    actualizar_lineas_pedido(pedido, lineas)
    vacio = pedido.comprobar_vacio()
    if vacio:
        pedido.borrar_datos_pedido()
        pedido.delete()
        return None
    pedido.actualizar_total()
    return pedido


def actualizar_lineas_pedido(pedido, lineas):
    for linea in lineas:
        id = linea["id"]
        objeto = get_linea_pedido(id)
        cantidad = linea["cantidad"]
        if id > 0 and objeto is None:
            raise ValidationError("No se ha encontrado al línea del pedido de id " + id)
        elif id == 0:
            objeto = crear_linea_pedido(pedido, linea)
        if cantidad == 0 and objeto is not None:
            objeto.delete()
        elif objeto is not None:
            objeto.cantidad = linea["cantidad"]

        if objeto is not None and objeto.id is not None:
            objeto.actualizar_total()
            objeto.save()


def get_linea_pedido(id):
    try:
        if id > 0:
            return PedidoLinea.objects.get(pk=id)
    except Pedido.DoesNotExist:
        return None
