from django.http.response import JsonResponse, HttpResponse
from backend.models import Producto
from .serializers import ProductoModalSerializer
from rest_framework.parsers import JSONParser
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def listar_productos(request):

    if request.method == "GET":
        productos = Producto.objects.all()
        serializer = ProductoModalSerializer(productos, many=True)
        return JsonResponse(serializer.data, safe=False)

    elif request.method == "POST":
        data = JSONParser().parse(request)
        serializer = ProductoModalSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)


@csrf_exempt
def ver_producto(request, id):
    try:
        producto = Producto.objects.get(pk=id)
    except Producto.DoesNotExist:
        return HttpResponse(status=404)

    if request.method == "GET":
        serializer = ProductoModalSerializer(producto)
        return JsonResponse(serializer.data)

    if request.method == "PUT":
        data = JSONParser().parse(request)
        serializer = ProductoModalSerializer(producto, data=data)

        if serializer.is_valid():
            serializer.save()
            return JsonResponse(serializer.data, status=201)
        return JsonResponse(serializer.errors, status=400)

    elif request.method == "DELETE":
        producto.delete()
        return HttpResponse(status=204)
