from rest_framework import mixins, serializers
from rest_framework import viewsets
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Producto, Usuario
from .serializers import UsuarioSerializer, ProductoSerializer




# Alta de usuario sin autorización  
class RegistroViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer

    def create(self, request, *args, **kwargs):
        serializer = UsuarioSerializer(data=request.data, context={'roles':request.data["roles"]})
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            usuario = buscar_usuario(serializer.data["id"])
            usuario.agregar_roles(request.data["roles"])
            usuario.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Abm de usuarios con autorización
class ABMUsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

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

def buscar_usuario(id):
    try:
        return Usuario.objects.get(pk=id)
    except Usuario.DoesNotExist:
        return None