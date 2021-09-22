from .models import Pedido, Estado
from .serializers import PedidoSerializer
from base.permisos import TieneRolComensal
from base.respuestas import Respuesta
from django.core.exceptions import ValidationError
from django.db import transaction
from gastronomia.repositorio import get_pedido, validar_crear_pedido, crear_pedido, actualizar_pedido, cerrar_pedido
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
    permission_classes = [IsAuthenticated, TieneRolComensal]

    def list(self, request, *args, **kwargs):
        idUsuario = request.query_params["usuario"]
        pedidos = Pedido.objects.filter(usuario=idUsuario).order_by('-fecha')
        if len(pedidos) > 0:
            serializer = PedidoSerializer(instance=pedidos, many=True)
            pedidos = serializer.data
        return respuesta.get_respuesta(datos=pedidos, formatear=False)

    @action(detail=False, methods=['get'])
    def listado_vendedor(self, request, pk=None):
        logueado = request.user
        pedidos = []
        if logueado.esVendedor:
            pedidos = Pedido.objects.all().order_by('-fecha')
        else:
            return respuesta.get_respuesta(False, "No está autorizado para listar los pedidos vendidos.", 401)
        if len(pedidos) > 0:
            serializer = PedidoSerializer(instance=pedidos, many=True)
            pedidos = serializer.data
        return respuesta.get_respuesta(datos=pedidos, formatear=False)

    def retrieve(self, request, *args, **kwargs):
        clave = kwargs.get('pk')
        pedido = None
        usuario = request.user
        serializer = None
        estado_valido = Estado.comprobar_estado_valido(clave)
        if estado_valido:
            pedido = get_pedido(pk=None, usuario=usuario, estado=clave)
            serializer = PedidoSerializer(instance=pedido)
        elif clave.isnumeric():
            pedido = get_pedido(pk=clave)
            serializer = PedidoSerializer(instance=pedido)
            return respuesta.get_respuesta(exito=True, datos=serializer.data)
        cerrado = None
        if pedido is None:
            cerrado = get_pedido(pk=None, usuario=usuario, estado=Estado.CERRADO)
        noHayAbierto = pedido is None
        hayCerrado = cerrado is not None
        if noHayAbierto and not hayCerrado:
            return respuesta.get_respuesta(False, "")
        if noHayAbierto and hayCerrado:
            return respuesta.get_respuesta(exito=True, datos={"cerrado": True})
        return respuesta.get_respuesta(True, "", None, serializer.data)

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

    def destroy(self, request, *args, **kwargs):
        super().destroy(request, *args, **kwargs)
        return respuesta.get_respuesta(True, "Pedido cancelado con éxito.")

    def update(self, request, *args, **kwargs):
        pedido = get_pedido(pk=kwargs["pk"])
        if pedido is None:
            return respuesta.get_respuesta(True, "No se ha encontrado el pedido.")
        cerrar_pedido(pedido)
        return respuesta.get_respuesta(True, "Pedido realizado con éxito, podrá retirarlo por el local en "
                                             "aproximadamente 45 minutos.")

    @action(detail=True, methods=['post'])
    def recibir(self, request, pk=None):
        try:
            pedido = get_pedido(pk)
            if pedido is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el pedido a marcar como "
                                                                    "recibido.")
            abierto = pedido.comprobar_estado_abierto()
            if abierto:
                return respuesta.get_respuesta(exito=False, mensaje="No se puede marcar como recibido el pedido "
                                                                    "debido a que el usuario no lo ha cerrado.")
            recibido = pedido.comprobar_estado_recibido()
            if recibido:
                return respuesta.get_respuesta(exito=False, mensaje="El pedido ya se encuentra en estado recibido.")
            cerrado = pedido.comprobar_estado_cerrado()
            if cerrado:
                pedido.recibir_pedido()
            else:
                raise ValidationError("")
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha recibido con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al recibir el pedido.")

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
            pedido.agregar_estado(Estado.CANCELADO)
            pedido.save()
            return respuesta.get_respuesta(exito=True, mensaje="El pedido se ha cancelado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al recibir el pedido.")
