from django.core.exceptions import ValidationError
from .models import Pedido, PedidoLinea, Estado
from producto.repositorio import get_producto


# Devuelve un pedido por estado.
def get_pedido(pk=None, usuario=None, estado=None):
    try:
        if pk is not None:
            return Pedido.objects.get(pk=pk)
        if usuario is not None and estado is not None:
            return Pedido.objects.filter(ultimo_estado=estado, usuario=usuario).first()
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


def crear_pedido(usuario, lineas, tipo):
    pedido = get_pedido(usuario=usuario, estado=Estado.ABIERTO)
    if pedido is not None:
        id = pedido.id
        return actualizar_pedido(id, lineas)
    pedido = Pedido(usuario=usuario, ultimo_estado=Estado.ABIERTO, total=0, tipo=tipo)
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
    id_producto = item["producto"]["id"]
    existente = get_linea_pedido(id_pedido=pedido.id, id_producto=id_producto)
    if existente is not None:
        return existente
    producto = get_producto(item["producto"]["id"])
    if producto is None:
        raise Exception("No se ha encontrado el producto.")
    cantidad = item["cantidad"]
    if int(cantidad) == 0:
        return None
    linea = PedidoLinea(pedido=pedido, producto=producto, cantidad=cantidad)
    linea.actualizar_total()
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
        id_linea = linea["id"]
        id_pedido = pedido.id
        id_producto = linea["producto"]["id"]
        objeto = get_linea_pedido(id_pedido, id_producto)
        cantidad = linea["cantidad"]
        if objeto is None and id_linea > 0:
            raise ValidationError("No se ha encontrado al línea del pedido de id " + id_linea)
        elif id_linea == 0:
            objeto = crear_linea_pedido(pedido, linea)
        if cantidad == 0 and objeto is not None:
            objeto.delete()
        elif objeto is not None:
            objeto.cantidad = linea["cantidad"]

        if objeto is not None and objeto.id is not None:
            objeto.actualizar_total()
            objeto.save()


def get_linea_pedido(id_pedido, id_producto):
    try:
        if id_pedido > 0 and id_producto > 0:
            return PedidoLinea.objects.get(producto=id_producto, pedido=id_pedido)
    except PedidoLinea.DoesNotExist:
        return None


def cerrar_pedido(pedido):
    pedido.agregar_estado(Estado.CERRADO)
    pedido.save()
    return pedido
