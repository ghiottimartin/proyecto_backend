from .models import Mesa
from .serializers import MesaSerializer
from .repositorio import comprobar_numero_repetido, crear_mesa, actualizar_mesa
from base import respuestas
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

        mesa = crear_mesa(numero, descripcion)
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
        actualizar_mesa(mesa=mesa, numero=numero, descripcion=descripcion)
        if isinstance(mesa, Mesa):
            return respuesta.get_respuesta(exito=True, mensaje="La mesa se ha editado con éxito.")
        return respuesta.get_respuesta(exito=False, mensaje="Hubo un error al editar la mesa.")

    # Devuelve los filtros de la query.
    def get_filtros(self, request):
        filtros = {}

        # Agrega filtro por id de mesa y lo devuelve sin el resto.
        id = request.query_params.get('numero', "")
        if id is not None and id.isnumeric() and int(id) > 0:
            filtros = {
                "id": id
            }
            return filtros

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
        cantidad = Mesa.objects.filter(**filtros).count()
        return cantidad

    # Devuelve las mesas según los filtros de la query
    def filtrar_ingresos(self, request):
        filtros = self.get_filtros(request)
        id = filtros.get("id")
        id_valido = id is not None and int(id) > 0
        if id_valido:
            return Mesa.objects.filter(id=id)

        offset = filtros.get("offset")
        limit = filtros.get("limit")
        filtros.pop("offset")
        filtros.pop("limit")
        mesas = Mesa.objects.filter(**filtros).order_by('numero')[offset:limit]
        return mesas

    # Lista los ingresos aplicando los filtros.
    def list(self, request, *args, **kwargs):
        mesas = self.filtrar_ingresos(request)
        if len(mesas) > 0:
            serializer = MesaSerializer(instance=mesas, many=True)
            mesas = serializer.data

        cantidad = self.get_cantidad_registros(request)
        total = Mesa.objects.count()
        datos = {
            "total": total,
            "mesas": mesas,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        puede_borrarse = instance.comprobar_puede_borrarse()
        if not puede_borrarse:
            return respuesta.get_respuesta(False, "La mesa no puede borrase porque ya se han realizado turnos sobre"
                                                  "la misma.")
        instance.delete()
        return respuesta.get_respuesta(True, "La mesa se ha borrado con éxito")
