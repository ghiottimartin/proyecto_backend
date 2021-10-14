from base import respuestas
from base import utils
from base.permisos import TieneRolAdmin
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from .models import Producto, Categoria, Ingreso
from .repositorio import validar_crear_ingreso, crear_ingreso
from .serializers import ProductoSerializer, CategoriaSerializer, IngresoSerializer

respuesta = respuestas.Respuesta()


# Obtención de categorías sin autorización
class CategoriaViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,  mixins.RetrieveModelMixin):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


# Abm de categorías con autorización
class ABMCategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdmin]

    def destroy(self, request, *args, **kwargs):
        categoria = self.get_object()
        puede_borrarse = categoria.comprobar_puede_borrarse()
        if not puede_borrarse:
            return respuesta.get_respuesta(False, "La categoría no se puede borrar porque está relacionada con un "
                                                  "producto activo")

        instance = self.get_object()
        instance.borrado = True
        instance.save()
        return respuesta.get_respuesta(True, "La categoría se ha borrado con éxito")


# Obtención de productos sin autorización
class ProductoViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Producto.objects.filter(borrado=False).order_by('nombre')
    serializer_class = ProductoSerializer


# Abm de productos con autorización
class ABMProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdmin]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            errores = serializer.get_errores_lista()
            return respuesta.get_respuesta(False, "Hubo un error al crear el producto", None, errores)
        serializer.save()
        producto = serializer.instance
        producto_costo_validos = producto.comprobar_producto_costo_validos()
        if not producto_costo_validos:
            return respuesta.get_respuesta(False, "El costo del producto debe ser mayor que el precio del mismo.", None)
        producto.agregar_precio()
        producto.agregar_costo()
        return respuesta.get_respuesta(True, "Producto creado con éxito", None, serializer.data)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        producto = self.get_object()

        precio = float(request.data["precio_vigente"])
        producto.agregar_precio(precio)

        costo = float(request.data["costo_vigente"])
        producto.agregar_costo(costo)

        compra_directa = bool(request.data["compra_directa"])
        producto.compra_directa = compra_directa

        venta_directa = bool(request.data["venta_directa"])
        producto.venta_directa = venta_directa

        producto_costo_validos = producto.comprobar_producto_costo_validos(costo, precio)
        if not producto_costo_validos:
            return respuesta.get_respuesta(False, "El costo del producto debe ser mayor que el precio del mismo.", None)

        # Si cambia la imagen, borro la anterior.
        if "imagen" in request.data:
            producto.imagen.delete(False)

        serializer = self.get_serializer(producto, data=request.data, partial=False)
        valido = serializer.is_valid(raise_exception=False)
        if not valido:
            return respuesta.get_respuesta(False, "Hubo un error al actualizar el producto", None, serializer.get_errores_lista())

        serializer.save()
        return respuesta.get_respuesta(True, "El producto fue actualizado con éxito", None, serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        puede_borrarse = instance.comprobar_puede_borrarse()
        if not puede_borrarse:
            return respuesta.get_respuesta(False, "El producto no se puede borrar porque está relacionado con un pedido")

        super().destroy(self, request, *args, **kwargs)
        return respuesta.get_respuesta(True, "El producto se ha borrado con éxito")


# Abm de ingresos.
class ABMIngresoViewSet(viewsets.ModelViewSet):
    queryset = Ingreso.objects.all()
    serializer_class = IngresoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        datos = request.data
        try:
            validar_crear_ingreso(datos)
            lineas = datos["lineas"]
            usuario = request.user
            ingreso = crear_ingreso(usuario, lineas)
            if ingreso is not None:
                serializer = IngresoSerializer(instance=ingreso)
                datos = serializer.data
            else:
                return respuesta.get_respuesta(False, "Hubo un error al crear el ingreso")
            ingreso.crear_movimientos()
            return respuesta.get_respuesta(True, "", None, datos)
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
            "fecha__range": (desde, hasta),
        }

        # Agrega filtros por pedidos del usuario
        idUsuario = request.query_params.get('usuario', None)
        if idUsuario is not None and idUsuario.isnumeric() and int(idUsuario) > 0:
            filtros["usuario"] = idUsuario

        # Agrega filtro por estado
        estado = request.query_params.get('estado', "")
        if estado != "":
            filtros["anulado__isnull"] = True if estado == "anulado" else False

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
        cantidad = Ingreso.objects.filter(**filtros).count()
        return cantidad

    # Devuelve los ingresos según los filtros de la query
    def filtrar_ingresos(self, request):
        filtros = self.get_filtros(request)
        id = filtros.get("id")
        id_valido = id is not None and int(id) > 0
        if id_valido:
            return Ingreso.objects.filter(id=id)

        offset = filtros.get("offset")
        limit = filtros.get("limit")
        filtros.pop("offset")
        filtros.pop("limit")
        pedidos = Ingreso.objects.filter(**filtros).order_by('-fecha')[offset:limit]
        return pedidos

    # Lista los ingresos aplicando los filtros.
    def list(self, request, *args, **kwargs):
        ingresos = self.filtrar_ingresos(request)
        if len(ingresos) > 0:
            serializer = IngresoSerializer(instance=ingresos, many=True)
            ingresos = serializer.data

        cantidad = self.get_cantidad_registros(request)
        total = Ingreso.objects.count()
        datos = {
            "total": total,
            "ingresos": ingresos,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)
