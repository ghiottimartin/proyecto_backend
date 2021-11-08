from .models import Mesa
from .serializers import MesaSerializer
from .repositorio import comprobar_numero_repetido, crear_mesa, actualizar_mesa
from base import respuestas
from base.repositorio import buscar_mozos
from django.db import transaction
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from base.permisos import TieneRolAdmin

respuesta = respuestas.Respuesta()


class MesaViewSet(viewsets.ModelViewSet):
    """
        Se encarga del alta, edición y borrado de las mesas.
    """
    queryset = Mesa.objects.all()
    serializer_class = MesaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        numero = request.data.get('numero')
        repetido = comprobar_numero_repetido(numero)
        if repetido:
            proximo_disponible = "1"
            ultima = Mesa.objects.order_by('-numero').first()
            if isinstance(ultima, Mesa):
                proximo_disponible = str(ultima.numero + 1)
            return respuesta.get_respuesta(exito=False, mensaje="Ya existe una mesa con ese número. El próximo mayor "
                                                                "número disponible es el " + str(proximo_disponible))

        descripcion = request.data.get('descripcion')
        buscar = request.data.get('mozos')
        mozos = buscar_mozos(buscar)
        mesa = crear_mesa(numero, mozos, descripcion)
        if isinstance(mesa, Mesa):
            return respuesta.get_respuesta(exito=True, mensaje="La mesa se ha creado con éxito.")
        return respuesta.get_respuesta(exito=False, mensaje="Hubo un error al crear la mesa.")

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        mesa = self.get_object()
        if mesa is None:
            return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado la mesa")

        numero = request.data.get('numero')
        repetido = comprobar_numero_repetido(numero=numero, pk=mesa.id)
        if repetido:
            proximo_disponible = "1"
            ultima = Mesa.objects.order_by('-numero').first()
            if isinstance(ultima, Mesa):
                proximo_disponible = str(ultima.numero + 1)
            return respuesta.get_respuesta(exito=False, mensaje="Ya existe una mesa con ese número. El próximo mayor "
                                                                "número disponible es el " + str(proximo_disponible))

        descripcion = request.data.get('descripcion')
        buscar = request.data.get('mozos')
        mozos = buscar_mozos(buscar)
        actualizar_mesa(mesa=mesa, numero=numero, mozos=mozos, descripcion=descripcion)
        if isinstance(mesa, Mesa):
            return respuesta.get_respuesta(exito=True, mensaje="La mesa se ha editado con éxito.")
        return respuesta.get_respuesta(exito=False, mensaje="Hubo un error al editar la mesa.")

    def list(self, request, *args, **kwargs):
        # Falta implementación.
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)