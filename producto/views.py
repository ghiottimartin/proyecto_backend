from base import respuestas
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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            errores = serializer.get_errores_lista()
            return respuesta.get_respuesta(False, "Hubo un error al crear el producto", None, errores)
        serializer.save()
        producto = serializer.instance
        producto.agregar_precio()
        return respuesta.get_respuesta(True, "Producto creado con éxito", None, serializer.data)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        # Si cambia la imagen, borro la anterior.
        if "imagen" in request.data:
            instance.imagen.delete(False)

        serializer = self.get_serializer(instance, data=request.data, partial=False)
        valido = serializer.is_valid(raise_exception=False)
        if not valido:
            return respuesta.get_respuesta(False, "Hubo un error al actualizar el producto", None, serializer.get_errores_lista())

        serializer.save()
        return respuesta.get_respuesta(True, "El producto fue actualizado con éxito", None, serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.borrado = True
        instance.save()
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
