from .models import Pedido, Estado, Venta
from .serializers import PedidoSerializer, VentaSerializer
from base import utils
from base import email
from base.respuestas import Respuesta
from base.permisos import TieneRolAdmin, TieneRolAdminOVendedor
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import FileResponse
from gastronomia.repositorio import get_pedido, validar_crear_pedido, crear_pedido, actualizar_pedido, cerrar_pedido, \
    get_venta, validar_crear_venta, crear_venta, get_pdf_comanda
from gastronomia.serializers import LineaSerializer
import io
from reportlab.pdfgen import canvas
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

respuesta = Respuesta()


# Abm de pedidos con autorización
class PedidoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    # Devuelve los filtros de la query.
    def get_filtros(self, request):
        # Agrega filtro por id de pedido y lo devuelve sin el resto.
        id = request.query_params.get('numero', "")
        if id is not None and id.isnumeric() and int(id) > 0:
            filtros = {
                "id": id
            }
            return filtros

        # Agrega filtros por fecha desde y hasta
        desdeTexto = request.query_params.get('fechaDesde', "")
        hastaTexto = request.query_params.get('fechaHasta', "")
        desde = utils.get_fecha_string2objeto(desdeTexto)
        hasta = utils.get_fecha_string2objeto(hastaTexto, False)
        filtros = {
            "fecha__range": (desde, hasta),
        }

        # Agrega filtros por pedidos del usuario
        idUsuario = request.query_params.get('usuario', None)
        if idUsuario is not None and idUsuario.isnumeric() and int(idUsuario) > 0:
            filtros["usuario"] = idUsuario

        # Agrega filtro por estado
        estado = request.query_params.get('estado', "")
        estado_entregado = estado == Estado.ENTREGADO
        if estado_entregado:
            estado = Estado.RECIBIDO

        if estado != "":
            filtros["ultimo_estado"] = estado

        # Agrega filtro por usuario
        usuario = request.query_params.get('nombreUsuario', "")
        if usuario != "":
            filtros["usuario__first_name__icontains"] = usuario

        # Agrega filtros por número de página actual
        pagina = int(request.query_params.get('paginaActual', 1))
        registros = int(request.query_params.get('registrosPorPagina', 10))
        offset = (pagina - 1) * registros
        limit = offset + registros
        filtros["offset"] = offset
        filtros["limit"] = limit
        return filtros

    # Devuelve los cantidad de registros sin tener en cuenta la página actual.
    def get_cantidad_registros(self, request):
        filtros = self.get_filtros(request)
        id = filtros.get("id")
        if id is None:
            filtros.pop("offset")
            filtros.pop("limit")
        cantidad = Pedido.objects.filter(**filtros).count()
        return cantidad

    # Devuelve los pedidos según los filtros de la query
    def filtrar_pedidos(self, request):
        filtros = self.get_filtros(request)
        id = filtros.get("id")
        id_valido = id is not None and int(id) > 0
        if id_valido:
            return Pedido.objects.filter(id=id)

        offset = filtros.get("offset")
        limit = filtros.get("limit")
        filtros.pop("offset")
        filtros.pop("limit")
        pedidos = Pedido.objects.filter(**filtros).order_by('-fecha')[offset:limit]
        return pedidos

    # Listado de pedidos para un comensal
    def list(self, request, *args, **kwargs):
        pedidos = self.filtrar_pedidos(request)
        if len(pedidos) > 0:
            serializer = PedidoSerializer(instance=pedidos, many=True)
            pedidos = serializer.data

        idUsuario = request.query_params.get("usuario")
        cantidad = self.get_cantidad_registros(request)
        total = Pedido.objects.filter(usuario=idUsuario).count()
        datos = {
            "total": total,
            "pedidos": pedidos,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)

    # Listado de pedidos para un vendedor
    @action(detail=False, methods=['get'])
    def listado_vendedor(self, request, pk=None):
        logueado = request.user
        pedidos = []
        if logueado.esVendedor:
            pedidos = self.filtrar_pedidos(request)
        else:
            return respuesta.get_respuesta(False, "No está autorizado para listar los pedidos vendidos.", 401)
        if len(pedidos) > 0:
            serializer = PedidoSerializer(instance=pedidos, many=True)
            pedidos = serializer.data
        cantidad = self.get_cantidad_registros(request)
        total = Pedido.objects.count()
        datos = {
            "total": total,
            "pedidos": pedidos,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)

    # Devuelve un pedido por id.
    def retrieve(self, request, *args, **kwargs):
        clave = kwargs.get('pk')
        pedido = None
        usuario = request.user
        serializer = None
        estado_valido = Estado.comprobar_estado_valido(clave)
        if estado_valido and not isinstance(clave, int):
            pedido = get_pedido(pk=None, usuario=usuario, estado=clave)
            serializer = PedidoSerializer(instance=pedido)
        elif clave.isnumeric():
            pedido = get_pedido(pk=clave)
            serializer = PedidoSerializer(instance=pedido)
            return respuesta.get_respuesta(exito=True, datos=serializer.data)
        en_curso = None
        if pedido is None:
            en_curso = get_pedido(pk=None, usuario=usuario, estado=Estado.EN_CURSO)

        disponible = None
        if not en_curso:
            disponible = get_pedido(pk=None, usuario=usuario, estado=Estado.DISPONIBLE)

        hay_abierto = pedido is not None
        if hay_abierto:
            return respuesta.get_respuesta(exito=True, datos=serializer.data)

        hay_en_curso = en_curso is not None
        hay_disponible = disponible is not None

        es_delivery = False
        if hay_en_curso:
            es_delivery = en_curso.comprobar_tipo_delivery()

        datos = {
            "en_curso": hay_en_curso,
            "delivery": es_delivery,
            "disponible": hay_disponible,
        }
        return respuesta.get_respuesta(exito=True, datos=datos)

    # Crea un pedido.
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
            Crea un pedido.
            @param request:
            @param args:
            @param kwargs:
            @return:
        """
        usuario = request.user
        try:
            datos = request.data
            errores = validar_crear_pedido(datos)
            if len(errores) > 0:
                mensaje = "Se produjeron los siguientes errores: "
                mensaje += ''.join(errores)
                return respuesta.get_respuesta(exito=True, mensaje=mensaje)

            id = datos["id"] if "id" in datos else 0
            lineas = datos["lineas"]
            lineas_anteriores = lineas
            anteriores = []
            if id <= 0:
                pedido = crear_pedido(usuario, lineas)
            else:
                anterior = get_pedido(pk=id)
                anteriores = anterior.lineas.all()
                lineas_serializer = LineaSerializer(instance=anteriores, many=True)
                lineas_anteriores = lineas_serializer.data
                pedido = actualizar_pedido(id, lineas)

            if pedido is not None and not isinstance(pedido, Pedido) and len(pedido) > 0:
                mensaje = "Se produjeron los siguientes errores: "
                mensaje += ''.join(pedido)
                return respuesta.get_respuesta(exito=True, datos={'errores': mensaje})

            if pedido is None:
                for anterior in anteriores:
                    anterior.limpiar_stock()
            else:
                pedido.actualizar_stock(lineas_anteriores)
                pedido.save()
                serializer = PedidoSerializer(instance=pedido)
                datos = serializer.data
            return respuesta.get_respuesta(True, "", None, datos)
        except ValidationError as e:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al actualizar el pedido")

    # Borra un pedido por id.
    def destroy(self, request, *args, **kwargs):
        pedido = self.get_object()
        lineas = pedido.lineas.all()
        for linea in lineas:
            linea.limpiar_stock()
        super().destroy(request, *args, **kwargs)
        return respuesta.get_respuesta(True, "Pedido borrado con éxito.")

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        pedido = get_pedido(pk=kwargs["pk"])
        if pedido is None:
            return respuesta.get_respuesta(True, "No se ha encontrado el pedido.")

        cambio = request.query_params.get('cambio', '')
        if cambio != '':
            cambio = float(cambio)
        else:
            cambio = 0

        tipo = request.query_params.get('tipo', '')
        valido = pedido.comprobar_tipo_valido(tipo)
        if not valido:
            return respuesta.get_respuesta(exito=False, mensaje="Debe seleccionar un tipo de pedido: retiro en local "
                                                                "o delivery.")

        direccion = request.query_params.get('direccion', '')
        tipo_delivery = pedido.comprobar_tipo_delivery(tipo)
        if tipo_delivery and (not isinstance(direccion, str) or len(direccion) < 7):
            return respuesta.get_respuesta(exito=False, mensaje="La dirección debe tener mínimo 7 caracteres.")

        cerrar_pedido(pedido, cambio, tipo, direccion)
        mensaje = "Pedido realizado con éxito, se le notificará por email cuando esté listo. Tiempo aproximado 30min."
        if tipo_delivery:
            mensaje = "Pedido realizado con éxito, se le notificará por email cuando el cadete esté saliendo. Tiempo " \
                      "aproximado 40min. "
        email.enviar_email_pedido_cerrado(pedido, mensaje)
        return respuesta.get_respuesta(exito=True, mensaje=mensaje)

    # Cambia el estado del pedido a entregado. Es decir, el mismo fue recibido por el comensal.
    @action(detail=True, methods=['post'])
    def entregar(self, request, pk=None):
        try:
            pedido = get_pedido(pk)
            if pedido is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el pedido a actualizar.")
            abierto = pedido.comprobar_estado_abierto()
            if abierto:
                return respuesta.get_respuesta(exito=False, mensaje="No se puede marcar como entregado el pedido "
                                                                    "debido a que el usuario no lo ha cerrado.")
            recibido = pedido.comprobar_estado_recibido()
            if recibido:
                return respuesta.get_respuesta(exito=False, mensaje="El pedido ya se encuentra en estado entregado.")
            disponible = pedido.comprobar_estado_disponible()
            if disponible:
                pedido.entregar()
            else:
                return respuesta.get_respuesta(exito=False, mensaje="No se puede entregar el pedido porque no tiene "
                                                                    "estado disponible.")
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha entregado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al entregar el pedido.")

    # Cambia el estado del pedido a anulado.
    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        try:
            pedido = get_pedido(pk)
            if pedido is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el pedido a anular.")
            usuario = request.user
            puede_anular = pedido.comprobar_puede_anular(usuario)
            if not puede_anular:
                return respuesta.get_respuesta(exito=False, mensaje="No está habilitado para anular el pedido.")

            motivo = request.query_params.get('motivo', "")
            abierto = pedido.comprobar_estado_abierto()
            if not abierto and isinstance(motivo, str) and len(motivo) < 10:
                return respuesta.get_respuesta(exito=False, mensaje="Debe indicar un motivo de cancelación.")

            pedido.anular_venta()

            motivo_texto = motivo if motivo != "undefined" else ""
            motivo_cortado = motivo_texto[:240] if len(motivo_texto) > 240 else motivo_texto
            pedido.observaciones = motivo_cortado

            pedido.agregar_estado(Estado.ANULADO)

            lineas = pedido.lineas.all()
            for linea in lineas:
                linea.limpiar_stock()
            pedido.save()
            email.enviar_email_pedido_anulado(pedido)
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha anulado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al anular el pedido.")

    # Cambia el estado del pedido a disponible.
    @action(detail=True, methods=['post'])
    def disponible(self, request, pk=None):
        try:
            pedido = get_pedido(pk)
            if pedido is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el pedido a actualizar.")
            usuario = request.user
            puede_marcar_disponible = pedido.comprobar_puede_marcar_disponible(usuario)
            if not puede_marcar_disponible:
                return respuesta.get_respuesta(exito=False, mensaje="No está habilitado para actualziar el pedido.")

            pedido.agregar_estado(Estado.DISPONIBLE)
            pedido.crear_venta()
            pedido.save()
            email.enviar_email_pedido_disponible(pedido)
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha actualizado con éxito.")
        except Exception:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al actualizar  el pedido.")

    @action(detail=True, methods=['get'])
    def comanda(self, request, pk=None):
        pedido = get_pedido(pk)
        if pedido is None:
            return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el pedido.")

        return get_pdf_comanda(pedido=pedido)


# Abm de ventas.
class ABMVentaViewSet(viewsets.ModelViewSet):
    queryset = Venta.objects.all()
    serializer_class = VentaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdminOVendedor]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """
            Crea una venta.
            @param request:
            @param args:
            @param kwargs:
            @return:
        """
        datos = request.data
        try:
            validar_crear_venta(datos)
            lineas = datos["lineas"]
            usuario = request.user
            resultado = crear_venta(usuario, lineas)
            if isinstance(resultado, Venta):
                serializer = VentaSerializer(instance=resultado)
                datos = serializer.data
                return respuesta.get_respuesta(True, "", None, datos)
            else:
                mensaje = "Se produjeron los siguientes errores: "
                mensaje += ''.join(resultado)
                return respuesta.get_respuesta(exito=False, mensaje=mensaje)
        except ValidationError as e:
            return respuesta.get_respuesta(False, e.messages)

    # Devuelve los filtros de la query.
    def get_filtros(self, request):
        # Agrega filtro por id de ingreso y lo devuelve sin el resto.
        id = request.query_params.get('numero', "")
        if id is not None and id.isnumeric() and int(id) > 0:
            filtros = {
                "id": id
            }
            return filtros

        # Agrega filtros por fecha desde y hasta
        desdeTexto = request.query_params.get('fechaDesde', "")
        hastaTexto = request.query_params.get('fechaHasta', "")
        desde = utils.get_fecha_string2objeto(desdeTexto)
        hasta = utils.get_fecha_string2objeto(hastaTexto, False)
        filtros = {
            "auditoria_creado_fecha__range": (desde, hasta),
        }

        # Agrega filtros por ventas del usuario
        idUsuario = request.query_params.get('usuario', None)
        if idUsuario is not None and idUsuario.isnumeric() and int(idUsuario) > 0:
            filtros["usuario"] = idUsuario

        # Agrega filtros por tipo de venta
        tipo = request.query_params.get('tipo', '')
        if tipo != "":
            filtros["tipo"] = tipo

        # Agrega filtro por estado
        estado = request.query_params.get('estado', "")
        if estado != "":
            filtros["anulado__isnull"] = True if estado == "activo" else False

        # Agrega filtro por usuario
        usuario = request.query_params.get('nombreUsuario', "")
        if usuario != "":
            filtros["usuario__first_name__icontains"] = usuario

        # Agrega filtros por número de página actual
        pagina = int(request.query_params.get('paginaActual', 1))
        registros = int(request.query_params.get('registrosPorPagina', 10))
        offset = (pagina - 1) * registros
        limit = offset + registros
        filtros["offset"] = offset
        filtros["limit"] = limit
        return filtros

    # Devuelve los cantidad de registros sin tener en cuenta la página actual.
    def get_cantidad_registros(self, request):
        filtros = self.get_filtros(request)
        id = filtros.get("id")
        if id is None:
            filtros.pop("offset")
            filtros.pop("limit")
        cantidad = Venta.objects.filter(**filtros).count()
        return cantidad

    # Devuelve las ventas según los filtros de la query
    def filtrar_ingresos(self, request):
        filtros = self.get_filtros(request)
        id = filtros.get("id")
        id_valido = id is not None and int(id) > 0
        if id_valido:
            return Venta.objects.filter(id=id)

        offset = filtros.get("offset")
        limit = filtros.get("limit")
        filtros.pop("offset")
        filtros.pop("limit")
        ventas = Venta.objects.filter(**filtros).order_by('-auditoria_creado_fecha')[offset:limit]
        return ventas

    # Lista los ingresos aplicando los filtros.
    def list(self, request, *args, **kwargs):
        ventas = self.filtrar_ingresos(request)
        if len(ventas) > 0:
            serializer = VentaSerializer(instance=ventas, many=True)
            ventas = serializer.data

        cantidad = self.get_cantidad_registros(request)
        total = Venta.objects.count()
        datos = {
            "total": total,
            "ventas": ventas,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)

    # Anula la venta.
    @transaction.atomic
    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        try:
            venta = get_venta(pk)
            if venta is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado la venta a anular.")

            usuario = request.user
            puede_anular = venta.comprobar_puede_anular(usuario)
            if not puede_anular:
                return respuesta.get_respuesta(exito=False, mensaje="No está habilitado para anular la venta.")

            anulado = venta.comprobar_anulada()
            if anulado:
                return respuesta.get_respuesta(exito=False, mensaje="La venta ya se encuentra anulado.")

            venta.anular()
            venta.save()
            return respuesta.get_respuesta(exito=True, mensaje="La venta se ha anulado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al anular la venta.")

    @action(detail=True, methods=['get'])
    def pdf(self, request, pk=None):
        objeto = get_venta(pk)
        if objeto is None:
            return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado la venta a exportar.")

        objeto.actualizar_impresion_venta()

        serializer = VentaSerializer(instance=objeto)
        venta = serializer.data

        # Creo un buffer de salida
        buffer = io.BytesIO()

        # Creo pdf
        pdf = canvas.Canvas(buffer)

        # Defino título de pdf
        nombre = venta["nombre"]
        pdf.setTitle(nombre)

        # Defino tamaño de pdf
        lineas = venta["lineas"]
        width = 220
        height = 300 + len(lineas) * 45
        pdf.setPageSize((width, height))

        # Agrego línea id de venta
        id_venta = str(venta["id_texto_limpio"])
        pdf.setFont("Helvetica-Bold", 18)
        altura_id_venta = height - 25
        pdf.drawString(70, altura_id_venta, id_venta)

        # Agrego la fecha.
        pdf.setFont("Helvetica-Bold", 10)
        fecha_texto = "Fecha: " + venta['fecha_texto']
        altura_fecha = altura_id_venta - 25
        pdf.drawString(100, altura_fecha, fecha_texto)

        tipo_venta = venta['tipo_venta']
        tipo_venta_online = " (" + venta['tipo_venta_online'] + ")" if venta['tipo_venta_online'] != '' else ''
        tipo_venta_texto = "Tipo: " + tipo_venta + tipo_venta_online
        altura_fecha -= 15

        pdf.drawString(100, altura_fecha, tipo_venta_texto)

        # Agrego texto cantidad / precio unitario
        altura_cantidad = altura_fecha - 40
        altura_descripcion = altura_cantidad - 10
        pdf.drawString(5, altura_cantidad, "CANT ./ PRECIO UNIT.")
        pdf.drawString(5, altura_descripcion, "DESCRIPCION")
        pdf.drawString(170, altura_descripcion, "IMPORTE")

        altura_lineas = altura_descripcion - 15
        pdf.setFont("Helvetica", 10)
        for linea in lineas:
            cantidad = linea['cantidad']
            subtotal = linea['precio_texto']
            cantidad_precio = str(cantidad) + " x " + str(subtotal)
            pdf.drawString(5, altura_lineas, cantidad_precio)

            altura_lineas -= 15
            producto = linea['producto']
            id_producto = producto['id']
            nombre = producto['nombre']
            id_nombre = "(" + str(id_producto) + ")  " + nombre
            pdf.drawString(5, altura_lineas, id_nombre)

            total = str(linea['total_texto'])
            pdf.drawString(170, altura_lineas, total)

            altura_lineas -= 15

        total_texto = venta['total_texto']
        altura_total = altura_lineas - 15
        pdf.setFont("Helvetica-Bold", 11)
        pdf.drawString(105, altura_total, "TOTAL: " + total_texto)

        altura_total -= 15
        vuelto_texto = venta['vuelto_texto'] if 'vuelto_texto' in venta else ''
        if len(vuelto_texto) > 0:
            pdf.setFont("Helvetica", 9)
            pdf.drawString(105, altura_total, "Vuelto: " + vuelto_texto)

        altura_total -= 15
        direccion_texto = venta['direccion_texto'] if 'direccion_texto' in venta else ''
        if len(direccion_texto) > 0:
            pdf.setFont("Helvetica", 9)
            pdf.drawString(105, altura_total, "Dirección: " + direccion_texto)

        altura_actual = altura_total
        tipo = venta['tipo']
        pdf.setFont("Helvetica-Bold", 10)
        if tipo == Venta.MESA:
            id_mesa = str(objeto.turno.mesa_id)
            altura_actual -= 15
            pdf.drawString(5, altura_actual, "Mesa: " + id_mesa)

            altura_actual -= 15
            id_mozo = str(objeto.turno.mozo_id)
            pdf.drawString(5, altura_actual, "Mozo: " + id_mozo)

        if tipo == Venta.ONLINE:
            id_pedido = str(objeto.pedido_id)
            altura_actual -= 15
            pdf.drawString(5, altura_actual, "Pedido: " + id_pedido)

        if tipo == Venta.ALMACEN:
            altura_actual -= 15
            id_vendedor = str(objeto.auditoria_creador_id)
            pdf.drawString(5, altura_actual, "Cajero: " + id_vendedor)

        altura_actual -= 15
        pdf.drawString(5, altura_actual, "-----------------------------------------------------------------")

        altura_actual -= 15
        pdf.drawString(5, altura_actual, "Indique su Cond. de I.V.A al mozo,")

        altura_actual -= 15
        pdf.drawString(5, altura_actual, "para la correcta confección")

        altura_actual -= 15
        pdf.drawString(5, altura_actual, "del Ticket/Factura")

        altura_actual -= 15
        pdf.drawString(5, altura_actual, "-----------------------------------------------------------------")

        # Cierro y guardo el pdf
        pdf.showPage()
        pdf.save()

        # FileResponse sets the Content-Disposition header so that browsers
        # present the option to save the file.
        buffer.seek(0)

        # Defino nombre de archivo.
        file_name = nombre + ".pdf"
        return FileResponse(buffer, as_attachment=True, filename=file_name)

    @action(detail=True, methods=['get'])
    def comanda(self, request, pk=None):
        venta = get_venta(pk)
        if venta is None:
            return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado la venta a exportar.")

        venta.actualizar_impresion_mesa()
        return get_pdf_comanda(venta=venta)
