from django.core.exceptions import ValidationError
from .models import Producto, Ingreso, IngresoLinea, ReemplazoMercaderia, ReemplazoMercaderiaLinea


# Busca un producto por id.
def get_producto(pk):
    try:
        return Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return None


# Busca un ingreso por id.
def get_ingreso(pk):
    try:
        return Ingreso.objects.get(pk=pk)
    except Ingreso.DoesNotExist:
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
    ingreso.actualizar()
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
    costo = item["costo"]
    linea = IngresoLinea(ingreso=ingreso, producto=producto, cantidad=cantidad, costo=costo)
    linea.save()
    return linea


# Valida que los datos del reemplazo de mercadería
def validar_crear_reemplazo_mercaderia(datos):
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
            stock_nuevo = int(linea["stock_nuevo"]) if "stock_nuevo" in linea else 0
            if not isinstance(stock_nuevo, int) or int(stock_nuevo) < 0:
                raise ValidationError("El nuevo stock del producto debe tener un valor numérico mayor a cero.")


# Crea un nuevo reemplazo de mercadería.
def crear_reemplazo_mercaderia(usuario, lineas):
    reemplazo = ReemplazoMercaderia(usuario=usuario)
    reemplazo.save()
    for item in lineas:
        crear_linea_reemplazo(reemplazo, item)
    reemplazo.generar_movimientos()
    return reemplazo


# Crea una nueva línea de reemplazo de mercadería.
def crear_linea_reemplazo(reemplazo, item):
    id_producto = item["producto"]["id"]
    producto = get_producto(id_producto)
    if producto is None:
        raise ValidationError("No se ha encontrado el producto.")
    stock = producto.stock
    if stock <= 0:
        nombre = producto.nombre
        raise ValidationError("No hay stock del producto '" + nombre + "', por lo que no puede ser reemplazado.")
    stock_nuevo = item["stock_nuevo"]
    if int(stock_nuevo) < 0:
        return None
    reemplazo_completo = False
    if int(stock_nuevo) == 0:
        reemplazo_completo = True
    linea = ReemplazoMercaderiaLinea(reemplazo=reemplazo, producto=producto, stock_nuevo=stock_nuevo, stock_anterior=producto.stock, reemplazo_completo=reemplazo_completo)
    linea.save()
    return linea
