from backend.models import Producto
from .serializers import ProductoModalSerializer
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication


@api_view(['GET', 'POST'])
def listar_productos(request):

    if request.method == "GET":
        productos = Producto.objects.all()
        serializer = ProductoModalSerializer(productos, many=True)
        return Response(serializer.data)

    elif request.method == "POST":
        serializer = ProductoModalSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET',  'PUT', 'DELETE'])
@authentication_classes((SessionAuthentication, BasicAuthentication,))
@permission_classes((IsAuthenticated,))
def ver_producto(request, id):
    try:
        producto = Producto.objects.get(pk=id)
    except Producto.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        serializer = ProductoModalSerializer(producto)
        return Response(serializer.data)

    # Si la request tiene id actualiza la entidad
    if request.method == "PUT":
        serializer = ProductoModalSerializer(producto, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == "DELETE":
        producto.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
