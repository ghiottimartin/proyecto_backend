import datetime
from .models import Pedido, PedidoLinea, Estado, Venta, VentaLinea
from django.core.exceptions import ValidationError
from django.http import FileResponse
import io
from reportlab.pdfgen import canvas
from producto.repositorio import get_producto
from gastronomia.serializers import LineaSerializer


# Devuelve un pedido por estado.
def get_pedido(pk=None, usuario=None, estado=None):
    try:
        if pk is not None:
            return Pedido.objects.get(pk=pk)
        if usuario is not None and estado is not None:
            return Pedido.objects.filter(ultimo_estado=estado, usuario=usuario).first()
    except Pedido.DoesNotExist:
        return None


# Busca una venta por id.
def get_venta(pk):
    try:
        return Venta.objects.get(pk=pk)
    except Venta.DoesNotExist:
        return None


# Valida que los datos del pedido sean correctos.
def validar_crear_pedido(datos):
    id = datos["id"] if "id" in datos else 0
    errores = []
    if not isinstance(int(id), int) or int(id < 0):
        errores.append("El pedido no tiene los datos suficientes para ser guardado.")
        return errores

    lineas = datos["lineas"] if "lineas" in datos else list()
    if not isinstance(lineas, list):
        errores.append("Debe seleccionar al menos un producto.")
    else:
        for linea in lineas:
            try:
                id_producto = linea["producto"]["id"]
            except:
                id_producto = 0
            if id_producto <= 0:
                errores.append("No se ha encontrado el producto.")
            cantidad = int(linea["cantidad"]) if "cantidad" in linea else 0
            if not isinstance(cantidad, int):
                errores.append("La cantidad del producto debe tener un valor numérico.")
    return errores


def crear_pedido(usuario, lineas):
    pedido = get_pedido(usuario=usuario, estado=Estado.ABIERTO)
    if pedido is not None:
        id = pedido.id
        lineas_anteriore = pedido.lineas.all()
        lineas_serializer = LineaSerializer(instance=lineas_anteriore, many=True)
        lineas_anteriores = lineas_serializer.data
        return actualizar_pedido(id, lineas, lineas_anteriores)
    pedido = Pedido(usuario=usuario, ultimo_estado=Estado.ABIERTO, total=0)
    pedido.save()

    errores = []
    for item in lineas:
        linea = crear_linea_pedido(pedido, item)
        if not isinstance(linea, PedidoLinea):
            errores += linea

    if len(errores) > 0:
        return errores

    vacio = pedido.comprobar_vacio()
    if vacio:
        pedido.borrar_datos_pedido()
        pedido.delete()
        return None
    pedido.actualizar_total()
    return pedido


def crear_linea_pedido(pedido, item):
    errores = []
    id_producto = item["producto"]["id"]
    existente = get_linea_pedido(id_pedido=pedido.id, id_producto=id_producto)
    if existente is not None:
        return existente
    producto = get_producto(item["producto"]["id"])
    if producto is None:
        errores.append("No se ha encontrado el producto.")
    cantidad = item["cantidad"]
    if int(cantidad) == 0:
        return []
    tiene_stock = producto.comprobar_tiene_stock(cantidad)
    nombre = producto.nombre
    if not tiene_stock:
        errores.append("No hay suficiente stock a la venta para el producto '" + nombre)

    if len(errores) > 0:
        return errores

    linea = PedidoLinea(pedido=pedido, producto=producto, cantidad=cantidad)
    linea.actualizar_total()
    linea.save()
    return linea


def actualizar_pedido(id, lineas, anteriores):
    pedido = get_pedido(pk=id)
    errores = []
    if pedido is None:
        errores.append("No se ha encontrado el pedido.")
    errores = actualizar_lineas_pedido(pedido, lineas, anteriores)
    if not isinstance(errores, PedidoLinea) and len(errores) > 0:
        return errores

    vacio = pedido.comprobar_vacio()
    if vacio:
        pedido.borrar_datos_pedido()
        pedido.delete()
        return None
    pedido.actualizar_total()
    return pedido


def actualizar_lineas_pedido(pedido, lineas, anteriores):
    errores = []
    for linea in lineas:
        id_linea = linea["id"]
        id_pedido = pedido.id
        id_producto = linea["producto"]["id"]
        objeto = get_linea_pedido(id_pedido, id_producto)
        cantidad = linea["cantidad"]
        if objeto is None and id_linea > 0:
            errores.append("No se ha encontrado al línea del pedido de id " + id_linea)
        elif id_linea == 0:
            objeto = crear_linea_pedido(pedido, linea)
        if cantidad == 0 and objeto is not None:
            objeto.delete()
        elif objeto is not None:
            objeto.cantidad = linea["cantidad"]

        cantidad_anterior = 0
        for anterior in anteriores:
            id_producto_anterior = anterior["producto"]["id"]
            if id_producto == id_producto_anterior:
                cantidad_anterior = anterior["cantidad"]

        diferencia = cantidad - cantidad_anterior
        producto = objeto.producto
        tiene_stock = producto.comprobar_tiene_stock(diferencia)
        nombre = producto.nombre
        if not tiene_stock:
            objeto.cantidad = cantidad_anterior
            errores.append("No hay suficiente stock del producto '" + nombre)

        if objeto is not None and objeto.id is not None and len(errores) == 0:
            objeto.actualizar_total()
            objeto.save()

    return errores


def get_linea_pedido(id_pedido, id_producto):
    try:
        if id_pedido > 0 and id_producto > 0:
            return PedidoLinea.objects.get(producto=id_producto, pedido=id_pedido)
    except PedidoLinea.DoesNotExist:
        return None


def cerrar_pedido(pedido, cambio, tipo, direccion):
    pedido.tipo = tipo
    pedido.cambio = cambio
    pedido.direccion = direccion
    pedido.agregar_estado(Estado.EN_CURSO)
    pedido.save()

    usuario = pedido.usuario
    anterior = usuario.direccion
    if len(direccion) > 0 and len(anterior) == 0:
        usuario.direccion = direccion
        usuario.save()
    return pedido


# Valida que los datos de la venta sean correctos.
def validar_crear_venta(datos):
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


def crear_venta(usuario, lineas):
    """
        Crea una nueva venta.
        @param usuario: Usuario
        @param lineas: List
        @return: errores|Venta
    """
    errores = []
    venta = Venta(usuario=usuario)
    venta.save()
    for item in lineas:
        errores += crear_linea_venta(venta, item)

    if len(errores) > 0:
        return errores

    venta.actualizar()
    venta.crear_movimientos()
    venta.save()
    return venta


def crear_linea_venta(venta, item):
    """
        Crea una línea de venta.
        @param venta: Venta
        @param item: List
        @return: List Array con errores
    """
    errores = []

    id_producto = item["producto"]["id"]
    producto = get_producto(id_producto)
    if producto is None:
        raise ValidationError("No se ha encontrado el producto.")

    nombre = producto.nombre
    venta_directa = producto.venta_directa
    if not venta_directa:
        errores.append("El producto '" + nombre + "' no es de venta directa.")

    cantidad = item["cantidad"]
    if int(cantidad) == 0:
        return None

    tiene_stock = producto.comprobar_tiene_stock(cantidad)
    if not tiene_stock:
        stock = producto.stock
        errores.append("No hay suficiente stock a la venta para el producto '" + nombre + ", quedan " + str(stock) + ". ")

    if len(errores) > 0:
        return errores

    precio = producto.precio_vigente
    linea = VentaLinea(venta=venta, producto=producto, cantidad=cantidad, precio=precio)
    linea.save()

    return errores


def get_pdf_comanda(venta=None, turno=None, pedido=None):
    objeto = None
    distancia_titulo = 0
    if venta is not None:
        objeto = venta
        distancia_titulo = 65
    if turno is not None:
        objeto = turno
        distancia_titulo = 25
    if pedido is not None:
        objeto = pedido
        distancia_titulo = 60

    # Creo un buffer de salida
    buffer = io.BytesIO()

    # Creo pdf
    pdf = canvas.Canvas(buffer)

    # Defino título de pdf
    titulo = objeto.get_titulo_comanda()
    pdf.setTitle(titulo)

    # Defino tamaño de pdf
    lineas = objeto.get_lineas_comanda()
    cantidad = len(lineas)
    width = 300
    height = 150 + cantidad * 30
    pdf.setPageSize((width, height))

    # Agrego línea id de venta
    pdf.setFont("Helvetica-Bold", 15)
    height -= 25
    pdf.drawString(distancia_titulo, height, titulo)

    # Agrego la fecha.
    pdf.setFont("Helvetica-Bold", 10)
    fecha_texto = "Fecha: " + datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
    height -= 25
    pdf.drawString(90, height, fecha_texto)

    # Agrego texto cantidad / precio unitario
    height -= 40
    pdf.drawString(5, height, "CANTIDAD")
    pdf.drawString(170, height, "PRODUCTO")

    height -= 15
    pdf.setFont("Helvetica", 10)
    for linea in lineas:
        cantidad = linea.get_cantidad_comanda()
        pdf.drawString(5, height, str(cantidad))

        producto = linea.producto
        nombre = producto.nombre
        id_producto = producto.id
        id_nombre = "(" + str(id_producto) + ")  " + nombre
        pdf.drawString(140, height, id_nombre)

        height -= 15

    pdf.setFont("Helvetica-Bold", 10)
    if turno is not None:
        nro_mesa = turno.mesa.get_numero_texto()
        height -= 15
        pdf.drawString(5, height, "Mesa: " + nro_mesa)

        height -= 15
        mozo = turno.mozo
        pdf.drawString(5, height, "Mozo: " + mozo.first_name)

    if venta is not None:
        cajero = venta.auditoria_creador.first_name
        height -= 15
        pdf.drawString(5, height, "Cajero: " + cajero)
        pedido = venta.pedido

    if pedido is not None:
        height -= 15
        id_pedido = pedido.get_id_texto()
        pdf.drawString(5, height, "Pedido: " + id_pedido)

    # Cierro y guardo el pdf
    pdf.showPage()
    pdf.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.
    buffer.seek(0)

    # Defino nombre de archivo.
    file_name = titulo + ".pdf"
    return FileResponse(buffer, as_attachment=True, filename=file_name)
