from base import respuestas
from base import utils
from base.permisos import TieneRolAdmin
from django.core.exceptions import ValidationError
from django.db import transaction
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from .models import Producto, Categoria, Ingreso, MovimientoStock, ReemplazoMercaderia
from .repositorio import validar_crear_ingreso, crear_ingreso, get_ingreso, validar_crear_reemplazo_mercaderia, crear_reemplazo_mercaderia, get_reemplazo
from .serializers import ProductoSerializer, CategoriaSerializer, IngresoSerializer, MovimientoSerializer, ReemplazoMercaderiaSerializer

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

    # Devuelve los filtros de la query.
    def get_filtros(self, request):
        filtros = {}

        # Agrega filtros por nombre de producto
        nombre = request.query_params.get('nombre', "")
        if len(nombre) > 0:
            filtros["nombre__contains"] = nombre

        # Agrega filtros por categoría de producto
        categoria = request.query_params.get('categoria', None)
        if categoria is not None and categoria.isnumeric() and int(categoria) > 0:
            filtros["categoria"] = categoria

        # Agrega filtro por tipo
        tipo = request.query_params.get('tipo', "")
        if len(tipo) > 0 and tipo == 'compra':
            filtros["compra_directa"] = True
        elif tipo == 'venta':
            filtros["venta_directa"] = True

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
        cantidad = Producto.objects.filter(**filtros).count()
        return cantidad

    # Devuelve los ingresos según los filtros de la query
    def filtrar_productos(self, request):
        filtros = self.get_filtros(request)

        offset = filtros.get("offset")
        limit = filtros.get("limit")
        filtros.pop("offset")
        filtros.pop("limit")

        orden = request.query_params.get('orden', "nombre")
        if orden == 'categoria':
            orden = "categoria__nombre"

        direccion = request.query_params.get('direccion', "")
        direccion_texto = "" if direccion == "ASC" else "-"

        order_by = direccion_texto + orden

        productos = Producto.objects.filter(**filtros).order_by(order_by)[offset:limit]
        return productos

    # Lista los productos aplicando los filtros.
    def list(self, request, *args, **kwargs):
        productos = self.filtrar_productos(request)
        if len(productos) > 0:
            serializer = ProductoSerializer(instance=productos, many=True)
            productos = serializer.data

        cantidad = self.get_cantidad_registros(request)
        total = Producto.objects.count()
        datos = {
            "total": total,
            "productos": productos,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)


# Abm de productos con autorización
class ABMProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdmin]
    parser_classes = [MultiPartParser, FormParser]

    @transaction.atomic
    def create(self, request, *args, **kwargs):

        try:
            existente = Producto.objects.get(nombre=request.data.get('nombre'))
        except Producto.DoesNotExist:
            existente = None

        if isinstance(existente, Producto):
            return respuesta.get_respuesta(False, "Ya existe un producto con ese nombre")

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
        producto.actualizar_stock()
        return respuesta.get_respuesta(True, "Producto creado con éxito", None, serializer.data)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        producto = self.get_object()

        precio = float(request.data["precio_vigente"])
        producto.agregar_precio(nuevo=precio)

        costo = float(request.data["costo_vigente"])
        producto.agregar_costo(nuevo=costo)

        compra_directa = bool(request.data["compra_directa"])
        producto.compra_directa = compra_directa

        venta_directa = bool(request.data["venta_directa"])
        producto.venta_directa = venta_directa

        stock = int(request.data["stock"])
        producto.actualizar_stock(nueva=stock)

        stock_seguridad = int(request.data["stock_seguridad"])
        producto.stock_seguridad = stock_seguridad

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

        # Agrega filtros por ingresos del usuario
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

    # Anula el ingreso realizado.
    @transaction.atomic
    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        try:
            ingreso = get_ingreso(pk)
            if ingreso is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el ingreso a anular.")

            usuario = request.user
            puede_anular = ingreso.comprobar_puede_anular(usuario)
            if not puede_anular:
                return respuesta.get_respuesta(exito=False, mensaje="No está habilitado para anular el ingreso.")

            anulado = ingreso.comprobar_anulado()
            if anulado:
                return respuesta.get_respuesta(exito=False, mensaje="El ingreso ya se encuentra anulado.")

            ingreso.anular()
            ingreso.save()
            return respuesta.get_respuesta(exito=True, mensaje="El ingreso se ha anulado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al anular el ingreso.")


# Abm de movimientos de stock.
class MovimientoStockViewSet(viewsets.ModelViewSet):
    queryset = MovimientoStock.objects.all()
    serializer_class = MovimientoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdmin]

    # Devuelve los filtros de la query.
    def get_filtros(self, request):
        filtros = {}

        # Agrega filtros por fecha desde y hasta
        desdeTexto = request.query_params.get('fechaDesde', "")
        hastaTexto = request.query_params.get('fechaHasta', "")
        desde = utils.get_fecha_string2objeto(desdeTexto)
        hasta = utils.get_fecha_string2objeto(hastaTexto, False)
        filtros["auditoria_creado_fecha__range"] = (desde, hasta)

        # Agrega filtros por producto del movimiento
        producto = request.query_params.get('producto', None)
        if producto is not None and producto.isnumeric() and int(producto) > 0:
            filtros["producto"] = producto

        # Agrega filtros por usuario del movimiento
        usuario = request.query_params.get('usuario', None)
        if usuario is not None and len(str(usuario)) > 0:
            filtros["auditoria_creador__first_name__contains"] = usuario

        # Agrega filtros por ingreso del movimiento
        idIngreso = request.query_params.get('ingreso', None)
        if idIngreso is not None and idIngreso.isnumeric() and int(idIngreso) > 0:
            filtros["ingreso_linea__ingreso_id"] = idIngreso

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
        cantidad = MovimientoStock.objects.filter(**filtros).count()
        return cantidad

    # Devuelve los movimientos según los filtros de la query
    def filtrar_movimientos(self, request):
        filtros = self.get_filtros(request)

        offset = filtros.get("offset")
        limit = filtros.get("limit")
        filtros.pop("offset")
        filtros.pop("limit")

        movimientos = MovimientoStock.objects.filter(**filtros).order_by('-auditoria_creado_fecha')[offset:limit]
        return movimientos

    # Lista los productos aplicando los filtros.
    def list(self, request, *args, **kwargs):
        movimientos = self.filtrar_movimientos(request)
        if len(movimientos) > 0:
            serializer = MovimientoSerializer(instance=movimientos, many=True)
            movimientos = serializer.data

        cantidad = self.get_cantidad_registros(request)

        total = 0
        idIngreso = request.query_params.get('ingreso', None)
        producto = request.query_params.get('producto', None)
        if idIngreso is not None and idIngreso.isnumeric() and int(idIngreso) > 0:
            total = MovimientoStock.objects.filter(ingreso_linea__ingreso=idIngreso).count()
        elif producto is not None and producto.isnumeric() and int(producto) > 0:
            total = MovimientoStock.objects.filter(producto=producto).count()

        datos = {
            "total": total,
            "movimientos": movimientos,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)


# Abm de ingresos.
class ReemplazoMercaderiViewSet(viewsets.ModelViewSet):
    queryset = ReemplazoMercaderia.objects.all()
    serializer_class = ReemplazoMercaderiaSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, TieneRolAdmin]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        datos = request.data
        try:
            validar_crear_reemplazo_mercaderia(datos)
            lineas = datos["lineas"]
            usuario = request.user
            reemplazo = crear_reemplazo_mercaderia(usuario, lineas)
            if reemplazo is not None:
                serializer = ReemplazoMercaderiaSerializer(instance=reemplazo)
                datos = serializer.data
            else:
                return respuesta.get_respuesta(False, "Hubo un error al crear el reemplazo de mercadería")
            return respuesta.get_respuesta(True, "", None, datos)
        except ValidationError as e:
            return respuesta.get_respuesta(False, e.messages)

    # Devuelve los filtros de la query.
    def get_filtros(self, request):
        # Agrega filtro por id de reemplazo y lo devuelve sin el resto.
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

        # Agrega filtros por reemplazos del usuario
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
        cantidad = ReemplazoMercaderia.objects.filter(**filtros).count()
        return cantidad

    # Devuelve los reemplazos según los filtros de la query
    def filtrar_reemplazos(self, request):
        filtros = self.get_filtros(request)
        id = filtros.get("id")
        id_valido = id is not None and int(id) > 0
        if id_valido:
            return ReemplazoMercaderia.objects.filter(id=id)

        offset = filtros.get("offset")
        limit = filtros.get("limit")
        filtros.pop("offset")
        filtros.pop("limit")
        pedidos = ReemplazoMercaderia.objects.filter(**filtros).order_by('-fecha')[offset:limit]
        return pedidos

    # Lista los reemplazos aplicando los filtros.
    def list(self, request, *args, **kwargs):
        reemplazos = self.filtrar_reemplazos(request)
        if len(reemplazos) > 0:
            serializer = ReemplazoMercaderiaSerializer(instance=reemplazos, many=True)
            reemplazos = serializer.data

        cantidad = self.get_cantidad_registros(request)
        total = ReemplazoMercaderia.objects.count()
        datos = {
            "total": total,
            "reemplazos": reemplazos,
            "registros": cantidad
        }
        return respuesta.get_respuesta(datos=datos, formatear=False)

    # Anula el reemplazo de mercadería realizado.
    @transaction.atomic
    @action(detail=True, methods=['post'])
    def anular(self, request, pk=None):
        try:
            reemplazo = get_reemplazo(pk)
            if reemplazo is None:
                return respuesta.get_respuesta(exito=False, mensaje="No se ha encontrado el reemplazo de mercadería a anular.")

            usuario = request.user
            puede_anular = reemplazo.comprobar_puede_anular(usuario)
            if not puede_anular:
                return respuesta.get_respuesta(exito=False, mensaje="No está habilitado para anular el reemplazo de mercadería.")

            anulado = reemplazo.comprobar_anulado()
            if anulado:
                return respuesta.get_respuesta(exito=False, mensaje="El reemplazo de mercadería ya se encuentra anulado.")

            reemplazo.anular()
            reemplazo.save()
            return respuesta.get_respuesta(exito=True, mensaje="El reemplazo de mercadería se ha anulado con éxito.")
        except:
            return respuesta.get_respuesta(exito=False, mensaje="Ha ocurrido un error al anular el reemplazo de mercadería.")