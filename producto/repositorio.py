from django.core.exceptions import ValidationError
from .models import Producto, Ingreso, IngresoLinea


# Busca un producto por id.
def get_producto(pk):
    try:
        return Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return None


# Valida que los datos del ingreso sean correctos.
def validar_crear_ingreso(datos):
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
            precio = int(linea["precio"]) if "precio" in linea else 0
            if not isinstance(precio, int):
                raise ValidationError("El precio del producto debe tener un valor numérico.")


# Crea un nuevo ingreso.
def crear_ingreso(usuario, lineas):
    ingreso = Ingreso(usuario=usuario)
    ingreso.save()
    for item in lineas:
        crear_linea_ingreso(ingreso, item)
    ingreso.actualizar_total()
    return ingreso


# Crea una nueva línea de ingreso.
def crear_linea_ingreso(ingreso, item):
    id_producto = item["producto"]["id"]
    producto = get_producto(id_producto)
    if producto is None:
        raise ValidationError("No se ha encontrado el producto.")
    compra_directa = producto.compra_directa
    if not compra_directa:
        nombre = producto.nombre
        raise ValidationError("El producto '" + nombre + "' no es de compra directa.")
    cantidad = item["cantidad"]
    if int(cantidad) == 0:
        return None
    precio = item["precio"]
    linea = IngresoLinea(ingreso=ingreso, producto=producto, cantidad=cantidad, precio=precio)
    linea.save()
    return linea
