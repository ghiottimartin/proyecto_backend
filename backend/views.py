import re
from django.http.response import JsonResponse
from backend.models import Producto
from .serializers import ProductoSerializer
from rest_framework.parsers import JSONParser


def index(request):
    pass


def listar_productos(request):
    if request.method == "GET":
        productos = Producto.objects.all()
        serializer = ProductoSerializer(productos, many=True)
        return JsonResponse(serializer.data, safe=False)
    elif request.method == "POST":
        data = JSONParser().parse(request)
        serializer = ProductoSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)
