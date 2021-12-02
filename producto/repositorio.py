from django.core.exceptions import ValidationError
from .models import Producto, Ingreso, IngresoLinea, ReemplazoMercaderia, ReemplazoMercaderiaLinea


# Busca un producto por id.
def get_producto(pk):
    try:
        return Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return None


def get_producto_nombre(nombre):
    """
        Busca un producto por nombre
        @param nombre: str
        @return: Producto|None
    """
    try:
        return Producto.objects.get(nombre=nombre)
    except Producto.DoesNotExist:
        return None


# Busca un ingreso por id.
def get_ingreso(pk):
    try:
        return Ingreso.objects.get(pk=pk)
    except Ingreso.DoesNotExist:
        return None


# Busca un reemplazo de mercadería por id.
def get_reemplazo(pk):
    try:
        return ReemplazoMercaderia.objects.get(pk=pk)
    except ReemplazoMercaderia.DoesNotExist:
        return None


def get_errores_crear_producto(datos, producto=None):
    errores = []

    categoria = datos["categoria"] if "categoria" in datos else 0
    if not isinstance(int(categoria), int) or int(categoria) <= 0:
        errores.append("Debe seleccionar una categoría de productos.")

    nombre = datos["nombre"] if "nombre" in datos else ""
    if not isinstance(nombre, str) or len(nombre) == 0:
        errores.append("Debe indicar el nombre del producto.")

    repetido = get_producto_nombre(nombre)
    editar = producto.nombre if producto is not None else ""
    if repetido is not None and editar != nombre:
        errores.append("El nombre '" + nombre + "' ya existe.")

    compra_directa = datos["compra_directa"] if "compra_directa" in datos else ""
    if not isinstance(compra_directa, str) or (compra_directa != "true" and compra_directa != "false"):
        errores.append("Debe indicar si el producto es de compra directa o no.")

    venta_directa = datos["venta_directa"] if "venta_directa" in datos else ""
    if not isinstance(venta_directa, str) or (venta_directa != "true" and venta_directa != "false"):
        errores.append("Debe indicar si el producto es de venta directa o no.")

    compra_directa = True if datos["compra_directa"] == "true" else False
    venta_directa = True if datos["venta_directa"] == "true" else False
    if compra_directa == False and venta_directa == False:
        errores.append("El producto debe ser o de compra directa o venta directa.")

    stock = datos["stock"] if "stock" in datos else 0
    if not isinstance(int(stock), int):
        errores.append("Debe indicar el stock del producto.")

    stock_seguridad = datos["stock_seguridad"] if "stock_seguridad" in datos else 0
    if not isinstance(int(stock_seguridad), int):
        errores.append("Debe indicar la cantidad de alerta de stock del producto.")

    precio_vigente = datos["precio_vigente"] if "precio_vigente" in datos else 0
    if venta_directa and (not isinstance(float(precio_vigente), float) or float(precio_vigente) <= 0.00):
        errores.append("Debe indicar el precio del producto.")

    costo_vigente = datos["costo_vigente"] if "costo_vigente" in datos else 0
    if not isinstance(float(costo_vigente), float) or float(costo_vigente) <= 0.00:
        errores.append("Debe indicar el costo del producto.")

    if venta_directa and isinstance(float(costo_vigente), float) and isinstance(float(precio_vigente), float) and costo_vigente > precio_vigente:
        errores.append("El costo del producto debe ser mayor que el precio del mismo.")

    return errores


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
        egresos_validos = True
        ingresos_validos = True
        for linea in lineas:
            try:
                id_producto = linea["producto"]["id"]
            except:
                id_producto = 0
            if id_producto <= 0:
                raise ValidationError("El reemplazo no tiene los datos suficientes para ser guardado. No se ha "
                                      "encontrado el producto de id " + str(id_producto) + ".")

            cantidad_egreso = int(linea["cantidad_egreso"]) if "cantidad_egreso" in linea else 0
            if not isinstance(cantidad_egreso, int) or int(cantidad_egreso) < 0:
                egresos_validos = False

            cantidad_egreso = int(linea["cantidad_egreso"]) if "cantidad_egreso" in linea else 0
            if not isinstance(cantidad_egreso, int) or int(cantidad_egreso) < 0:
                egresos_validos = False

        if not egresos_validos or not ingresos_validos:
                raise ValidationError("Las cantidades de ingreso y egreso no pueden ser negativas")


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

    cantidad_egreso = item["cantidad_egreso"]
    if int(cantidad_egreso) < 0:
        return None

    cantidad_ingreso = item["cantidad_ingreso"]
    if int(cantidad_ingreso) < 0:
        return None

    stock_nuevo = stock + cantidad_ingreso - cantidad_egreso
    linea = ReemplazoMercaderiaLinea(
        reemplazo=reemplazo,
        producto=producto,
        stock_nuevo=stock_nuevo,
        stock_anterior=stock,
        cantidad_ingreso=cantidad_ingreso,
        cantidad_egreso=cantidad_egreso,
        reemplazo_completo=False
    )
    linea.save()
    return linea
