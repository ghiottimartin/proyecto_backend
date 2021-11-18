from .models import Mesa
from django.core.exceptions import ValidationError


def buscar_mesa(pk):
    """
        Busca una mesa por id.
        @param pk: int
        @return: Mesa|null
    """
    try:
        mesa = Mesa.objects.get(pk=pk)
    except Mesa.DoesNotExist:
        return None
    return mesa


def comprobar_numero_repetido(numero, pk=0):
    """
        Comprueba que el número de mesa no esté repetido
        @param numero: Número a buscar
        @param pk:  Id de la mesa que desea asignarse el número.
        @return: Boolean
    """
    repetida = Mesa.objects.filter(numero=numero).first()
    existe = isinstance(repetida, Mesa)
    return (existe and pk == 0) or (existe and pk > 0 and repetida.id != pk)


def crear_mesa(numero, descripcion=""):
    """
        Crea una nueva instancia de una mesa.
        @param numero: Número de la mesa.
        @param descripcion: Descrición de la mesa opcional.
        @return: Mesa
    """
    mesa = Mesa(numero=numero, descripcion=descripcion)
    mesa.save()
    return mesa


def actualizar_mesa(mesa, numero, descripcion=""):
    """
        Actualiza los datos de la mesa.
        @param mesa: Mesa
        @param numero: int
        @param descripcion: str
        @return: void
    """
    mesa.numero = numero
    mesa.descripcion = descripcion
    mesa.save()


def get_mesa(pk=None):
    """
        Busca y devuelve una mesa por id, si no la encuentra devuelve none
        @param pk: Mesa
        @return: Mesa|None
    """
    try:
        mesa = Mesa.objects.get(pk=pk)
    except Mesa.DoesNotExist:
        return None
    return mesa


def comprobar_ordenes_validas(ordenes):
    """
        Comprueba que las órdenes contengan los datos suficientes para ser guardadas.
        @param ordenes: List
        @return:
    """
    for orden in ordenes:
        try:
            id_producto = orden["producto"]["id"]
        except:
            id_producto = 0
        if id_producto <= 0:
            raise ValidationError("No se ha encontrado el producto.")
        cantidad = int(orden["cantidad"]) if "cantidad" in orden else 0
        if not isinstance(cantidad, int):
            raise ValidationError("La cantidad del producto debe tener un valor numérico.")