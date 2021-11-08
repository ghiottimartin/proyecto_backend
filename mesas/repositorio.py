from .models import Mesa


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


def crear_mesa(numero, mozos, descripcion=""):
    """
        Crea una nueva instancia de una mesa, agregando los mozos encargados a la mesa.
        @param numero: Número de la mesa.
        @param mozos: Mozos a agregar como responsables de la misma.
        @param descripcion: Descrición de la mesa opcional.
        @return: Mesa
    """
    mesa = Mesa(numero=numero, descripcion=descripcion)
    mesa.save()
    mesa.agregar_mozos(mozos)
    return mesa


def actualizar_mesa(mesa, numero, mozos, descripcion=""):
    """
        Actualiza los datos de la mesa.
        @param mesa: Mesa
        @param numero: int
        @param mozos: List
        @param descripcion: str
        @return: void
    """
    mesa.actualizar_mozos(mozos)
    mesa.numero = numero
    if descripcion != "":
        mesa.descripcion = descripcion
    mesa.save()
