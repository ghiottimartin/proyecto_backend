from producto.models import Producto


# Busca un producto por id.
def get_producto(pk):
    try:
        return Producto.objects.get(pk=pk)
    except Producto.DoesNotExist:
        return None