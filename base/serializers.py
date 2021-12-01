from rest_framework import serializers
from rest_framework.authtoken.views import Token
from .models import Usuario, Rol
import secrets


# ModelSerializer que permite devolver los mensajes en forma de lista de cadenas de texto.
class CustomModelSerializer(serializers.ModelSerializer):

    def get_errores_lista(self, errores=None):
        mensajes = []
        if errores is None:
            errores = self.errors
        for key in errores:
            error = errores[key][0]
            if isinstance(error, str):
                texto = key.capitalize() + ": " + error.capitalize()
                mensajes.append(texto)
            elif isinstance(error, dict):
                recursivos = self.get_errores_lista(error)
                mensajes = mensajes + recursivos
        return mensajes


# Serializador de los roles del usuario.
class RolSerializer(serializers.ModelSerializer):
    class Meta:
        model = Rol
        fields = '__all__'


# Serializador del usuario.
class UsuarioSerializer(CustomModelSerializer):
    roles = RolSerializer(many=True, read_only=True)
    operaciones_listado = serializers.SerializerMethodField()

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'roles', 'habilitado', 'password', 'dni', 'operaciones',
                  'esAdmin', 'esMozo', 'esComensal', 'esVendedor', 'observaciones', 'operaciones_listado', 'direccion']

    # Método que devuelve los datos del usuario. Quito la contraseña para que no sea mostrada al usuario.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['password'] = ""
        ret['puede_deshabilitarse'] = instance.habilitado
        ret['puede_habilitarse'] = not instance.habilitado
        ret['habilitado_texto'] = "Activo" if instance.habilitado else "Deshabilitado"

        estado = "text-success" if instance.habilitado else "text-danger"
        ret['habilitado_clase'] = estado + " font-weight-bold"
        return ret

    # Devuelve las operaciones disponibles para el usuario actual.
    def get_operaciones_listado(self, objeto):
        operaciones = []

        accion = 'editar'
        operaciones.append({
            'accion': accion,
            'clase': 'btn btn-sm btn-success text-success',
            'texto': 'Editar',
            'icono': 'fas fa-pencil-alt',
            'title': 'Editar Usuario ' + objeto.get_id_texto(),
            'key': str(objeto.id) + "-" + accion,
        })

        puede_borrar = objeto.comprobar_puede_borrarse()
        if puede_borrar:
            accion = 'borrar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-danger text-danger',
                'texto': 'Borrar',
                'icono': 'fas fa-trash-alt',
                'title': 'Borrar Usuario ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        habilitado = objeto.habilitado
        if habilitado:
            accion = 'deshabilitar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-secondary text-secondary',
                'texto': 'Deshabilitar',
                'icono': 'fas fa-ban',
                'title': 'Deshabilitar Usuario ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })
        else:
            accion = 'habilitar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-primary text-primary',
                'texto': 'Habilitar',
                'icono': 'fas fa-trash-alt',
                'title': 'Habilitar Usuario ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        return operaciones

    # Método de creación de un usuario.
    def create(self, validated_data):
        user = Usuario.objects.create_user(**validated_data)
        user.token_email = secrets.token_hex(16)
        user.save()
        Token.objects.create(user=user)
        return user
