from backend import respuestas
from rest_framework import mixins
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from .models import Producto, Categoria
from .serializers import ProductoSerializer, CategoriaSerializer


# Obtención de categorías sin autorización
class CategoriaViewSet(viewsets.GenericViewSet, mixins.ListModelMixin,  mixins.RetrieveModelMixin):
    queryset = Categoria.objects.all()
    serializer_class = CategoriaSerializer


# Obtención de productos sin autorización
class ProductoViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer


# Abm de productos con autorización
class ABMProductoViewSet(viewsets.ModelViewSet):
    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid(raise_exception=False):
            errores = serializer.get_errores_lista()
            return respuestas.get_respuesta(False, "Hubo un error al crear el producto", None, errores)
        serializer.save()
        return respuestas.get_respuesta(True, "Producto creado con éxito", None, serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return respuestas.get_respuesta(True, "El producto se ha borrado con éxito")
