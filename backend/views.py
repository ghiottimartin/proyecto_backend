from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import mixins
from rest_framework import status
from rest_framework import viewsets
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import UsuarioSerializer, ProductoSerializer
from .models import Producto

# Registro
@api_view(['POST'])
def registro(request):
    if request.method == "POST":
        data = request.data
        serializer = UsuarioSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# Obtener un usuario o todos los usuarios
@authentication_classes((TokenAuthentication))
@permission_classes((IsAuthenticated))
class UsuarioApiView(APIView):
    def get(self, request, id=None):
        if id == None:
            usuarios = User.objects.all()
            serializer = UsuarioSerializer(usuarios, many=True)
            return Response(serializer.data)
        usuario = get_object_or_404(User, pk=id)
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)

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