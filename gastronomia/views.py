from .models import Pedido, Estado
from .serializers import PedidoSerializer
from base.permisos import TieneRolComensal
from base.respuestas import Respuesta
from django.core.exceptions import ValidationError
from django.db import transaction
from gastronomia.repositorio import get_pedido, validar_crear_pedido, crear_pedido, actualizar_pedido, finalizar_pedido
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

respuesta = Respuesta()


# Abm de pedidos con autorización
class PedidoEstadoViewSet(viewsets.ModelViewSet):
    queryset = Pedido.objects.all()
    serializer_class = PedidoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolComensal]

    def retrieve(self, request, *args, **kwargs):
        clave = kwargs.get('pk')
        pedido = None
        usuario = request.user
        if isinstance(clave, str):
            pedido = get_pedido(pk=None, usuario=usuario, estado=clave)
        if isinstance(clave, int):
            pedido = get_pedido(pk=clave)
        finalizado = None
        if pedido is None:
            finalizado = get_pedido(pk=None, usuario=usuario, estado=Estado.FINALIZADO)
        noHayAbierto = pedido is None
        hayFinalizado = finalizado is not None
        if noHayAbierto and not hayFinalizado:
            return respuesta.get_respuesta(False, "")
        if noHayAbierto and hayFinalizado:
            return respuesta.get_respuesta(exito=True, datos={"finalizado": True})
        serializer = PedidoSerializer(instance=pedido)
        return respuesta.get_respuesta(True, "", None, serializer.data)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        usuario = request.user
        try:
            datos = request.data
            validar_crear_pedido(datos)
            id = datos["id"]
            lineas = datos["lineas"]
            if id <= 0:
                pedido = crear_pedido(usuario, lineas)
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
        finalizar_pedido(pedido)
        return respuesta.get_respuesta(True, "Pedido realizado con éxito, podrá retirarlo por el local en "
                                             "aproximadamente 45 minutos.")
