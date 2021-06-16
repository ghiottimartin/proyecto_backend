from .models import Pedido, Estado
from .serializers import PedidoSerializer
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from base.permisos import TieneRolComensal
from base import respuestas


# Devuelve un pedido por estado.
def get_pedido(pk=None, usuario=None, estado=None):
    try:
        if pk is not None:
            return Pedido.objects.get(pk=pk)
        if usuario is not None and estado is not None:
            return Pedido.objects.get(ultimo_estado=estado, usuario=usuario)
    except Pedido.DoesNotExist:
        return None


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
            pedido = get_pedido(usuario=usuario, estado=clave)
        if isinstance(clave, int):
            pedido = get_pedido(pk=clave)
        exito = pedido is not None
        return respuestas.get_respuesta(exito, "", None, pedido)



