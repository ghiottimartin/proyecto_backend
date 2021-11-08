from django.db import models
from base.models import Auditoria, Usuario


class Mesa(Auditoria, models.Model):
    """
        Representa una mesa que posee mozos y turnos.
    """

    OCUPADA = "ocupada"
    DESOCUPADA = "desocupada"

    mozos = models.ManyToManyField(to=Usuario, related_name="mesas_mozos", blank=True)
    numero = models.BigIntegerField()
    estado = models.CharField(max_length=10, default=DESOCUPADA)
    descripcion = models.CharField(max_length=100)

    def get_numero_texto(self):
        """
            Devuelve el número legible de la mesa en formato #00052
        """
        numero = self.numero
        return "#" + str(numero).zfill(5)

    def agregar_mozos(self, mozos):
        """
            Agrega los mozos a la colección de mozos de la mesa.
            @param mozos:
            @return: None
        """
        for mozo in mozos:
            self.agregar_mozo(mozo)
        self.save()

    def agregar_mozo(self, mozo):
        """
            Agrega el mozo a la colección de mozos, si es que está repetido.
            @param mozo: Usuario
            @return: None
        """
        ultimo = self.mozos.filter(id=mozo.id).first()
        if not isinstance(ultimo, Usuario):
            self.mozos.add(mozo)

    def comprobar_tiene_mozo(self, buscar, mozos=None):
        """
            Comprueba si el mozo pertenece a la mesa actual.
            @param mozo: Usuario
            @return: bool
        """
        coleccion = self.mozos.all()
        if mozos is None:
            mozo = coleccion.filter(id=buscar.id).first()
            return mozo is not None
        else:
            existe = False
            for mozo in mozos:
                existe = mozo.id == buscar.id
                if existe:
                    return True
        return False

    def quitar_mozo(self, mozo):
        """
            Quita el mozo actual de la colección de mozos.
            @param mozo: Mozo
            @return:  void
        """
        existe = self.mozos.filter(id=mozo.id).first()
        if existe:
            self.mozos.remove(existe)

    def actualizar_mozos(self, mozos):
        """
            Actualiza los mozos de la mesa en base a la colección de mozos.
            @param mozos: List
            @return: void
        """
        actuales = self.mozos.all()
        for actual in actuales:
            existe = self.comprobar_tiene_mozo(actual, mozos)
            if not existe:
                self.quitar_mozo(actual)

        for mozo in mozos:
            existe = self.comprobar_tiene_mozo(mozo)
            if not existe:
                self.agregar_mozo(mozo)
