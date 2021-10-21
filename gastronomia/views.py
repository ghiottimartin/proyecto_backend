from .models import Pedido, Estado
from .serializers import PedidoSerializer
from base.respuestas import Respuesta
from django.core.exceptions import ValidationError
from django.db import transaction
from gastronomia.repositorio import get_pedido, validar_crear_pedido, crear_pedido, actualizar_pedido, cerrar_pedido
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from base import utils

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
            filtros["usuario__first_name__contains"] = usuario

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
        no_hay_abierto = pedido is None
        hay_en_curso = en_curso is not None
        if no_hay_abierto and hay_en_curso:
            return respuesta.get_respuesta(exito=True, datos={"en_curso": True})

        disponible = get_pedido(pk=None, usuario=usuario, estado=Estado.DISPONIBLE)
        hay_disponible = disponible is not None
        if no_hay_abierto and hay_disponible:
            return respuesta.get_respuesta(exito=True, datos={"disponible": True})

        if no_hay_abierto and not hay_en_curso and not hay_disponible:
            return respuesta.get_respuesta(False, "")
        return respuesta.get_respuesta(True, "", None, serializer.data)

    # Crea un pedido.
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        usuario = request.user
        try:
            tipo = Pedido.TIPO_ONLINE
            datos = request.data
            validar_crear_pedido(datos)
            id = datos["id"]
            lineas = datos["lineas"]
            if id <= 0:
                pedido = crear_pedido(usuario, lineas, tipo)
            else:
                pedido = actualizar_pedido(id, lineas)
            datos = {"pedido": "borrado"}
            if pedido is not None:
                serializer = PedidoSerializer(instance=pedido)
                datos = serializer.data
            return respuesta.get_respuesta(True, "", None, datos)
        except ValidationError as e:
            return respuesta.get_respuesta(False, e.messages)

    # Borra un pedido por id.
    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return respuesta.get_respuesta(True, "Pedido borrado con éxito.")

    # Cambia el estado del pedido a en curso.
    def update(self, request, *args, **kwargs):
        pedido = get_pedido(pk=kwargs["pk"])
        if pedido is None:
            return respuesta.get_respuesta(True, "No se ha encontrado el pedido.")
        cerrar_pedido(pedido)
        return respuesta.get_respuesta(True, "Pedido realizado con éxito, podrá retirarlo por el local en "
                                             "aproximadamente 45 minutos.")

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
                pedido.entregar_pedido()
            else:
                return respuesta.get_respuesta(exito=False, mensaje="No se puede entregar el pedido porque no tiene "
                                                                    "estado disponible.")
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha entregado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al entregar el pedido.")

    # Cambia el estado del pedido a cancelado.
    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        try:
            pedido = get_pedido(pk)
            if pedido is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el pedido a cancelar.")
            usuario = request.user
            puede_cancelar = pedido.comprobar_puede_cancelar(usuario)
            if not puede_cancelar:
                return respuesta.get_respuesta(exito=False, mensaje="No está habilitado para cancelar el pedido.")

            motivo = request.query_params.get('motivo', "")
            abierto = pedido.comprobar_estado_abierto()
            if not abierto and isinstance(motivo, str) and len(motivo) < 10:
                return respuesta.get_respuesta(exito=False, mensaje="Debe indicar un motivo de cancelación.")
            pedido.observaciones = motivo if motivo != "undefined" else ""
            pedido.agregar_estado(Estado.CANCELADO)
            pedido.save()
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha cancelado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al cancelar el pedido.")

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
            pedido.save()
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha actualizado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al actualizar  el pedido.")
