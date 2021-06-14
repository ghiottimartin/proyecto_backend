import uuid


# Define la ruta y el nombre del archivo para la imagen de un producto.
def get_ruta_nombre_archivo(instance, filename):
    return 'producto/{id}-{filename}'.format(id=uuid.uuid4(), filename=filename)