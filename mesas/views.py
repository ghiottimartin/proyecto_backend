from .models import Mesa, Turno
from .serializers import MesaSerializer, TurnoSerializer
from .repositorio import comprobar_numero_repetido, crear_mesa, actualizar_mesa, get_mesa, comprobar_ordenes_validas
from base import respuestas
from base.repositorio import get_usuario
from django.db import transaction
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
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
        numero = request.data.get('numero', '')
        if numero.isnumeric() and (numero == 0 or numero == '0'):
            return respuesta.get_respuesta(exito=False, mensaje="El número de la mesa debe ser mayor a cero.")

        repetido = comprobar_numero_repetido(numero)
        if repetido:
            proximo_disponible = "1"
            ultima = Mesa.objects.order_by('-numero').first()
            if isinstance(ultima, Mesa):
                proximo_disponible = str(ultima.numero + 1)
            return respuesta.get_respuesta(exito=False, mensaje="Ya existe una mesa con ese número. El próximo mayor "
                                                                "número disponible es el " + str(proximo_disponible))

        descripcion = request.data.get('descripcion', '')

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

        # Agrega filtro por número de mesa.
        numero = request.query_params.get('numero', "")
        if numero is not None and numero.isnumeric() and int(numero) > 0:
            filtros["numero"] = numero

        # Agrega filtro por estado de mesa.
        estado = request.query_params.get('estado', "")
        if estado is not None and isinstance(estado, str) and (estado == Mesa.DISPONIBLE or estado == Mesa.OCUPADA):
            filtros["estado"] = estado

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
    def filtrar_mesas(self, request):
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

    # Lista las mesas aplicando los filtros.
    def list(self, request, *args, **kwargs):
        mesas = self.filtrar_mesas(request)
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


class TurnoViewSet(viewsets.ModelViewSet):
    """
        Se encarga del alta, edición y borrado de los turno.
    """
    queryset = Turno.objects.all()
    serializer_class = TurnoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        pk = request.data.get('id_mesa', 0)
        mesa = get_mesa(pk)
        if mesa is None:
            return respuesta.get_respuesta(False, "No se encontró la mesa para crear el turno, intente recargar la "
                                                  "página.")
        nombre = request.data.get('first_name')
        turno = mesa.crear_turno(nombre)
        if isinstance(turno, Turno):
            datos = MesaSerializer(instance=mesa)
            mesa_json = datos.data
            datos = {
                "mesa": mesa_json
            }
            return respuesta.get_respuesta(exito=True, datos=datos, mensaje="El turno se creó con éxito.")
        return respuesta.get_respuesta(False, "Hubo un error al crear el turno.")

    @transaction.atomic
    def update(self, request, pk=None, *args, **kwargs):
        """
            Guarda el turno en estado borrador actualizando las órdenes del mismo
            @param request:
            @param pk:
            @param args:
            @param kwargs:
            @return:
        """
        turno = self.get_object()
        if turno is None:
            return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el turno a guardar.")

        ordenes = request.data.get('ordenes')
        comprobar_ordenes_validas(ordenes)
        turno.agregar_editar_ordenes(ordenes)
        turno.save()

        mozo_buscar = request.data.get('mozo')
        mozo_id = mozo_buscar["id"]
        mozo = get_usuario(pk=mozo_id)
        if mozo is None:
            return respuesta.get_respuesta(exito=False, mensaje="Debe seleccionar un mozo para el turno actual.")
        turno.mozo = mozo
        turno.save()
        return respuesta.get_respuesta(exito=True, mensaje="El turno se actualizó con éxito.")

    @action(detail=True, methods=['delete'])
    def cancelar(self, request):
        turno = self.get_object()
        cancelado = turno.comprobar_cancelado()
        if cancelado:
            return respuesta.get_respuesta(exito=False, mensaje="El turno ya se encuentra cancelado.")
        turno.cancelar()
        return respuesta.get_respuesta(exito=True, mensaje="El turno se canceló con éxito.")

    @action(detail=True, methods=['put'])
    def cerrar(self, request):
        self.update(request)
        turno = self.get_object()
        puede = turno.comprobar_puede_cerrar()
        if not puede:
            mensaje = turno.get_razon_no_puede_cerrar()
            return respuesta.get_respuesta(exito=False, mensaje=mensaje)
        turno.cerrar()
        return respuesta.get_respuesta(exito=True, mensaje="El turno se cerró con éxito.")
