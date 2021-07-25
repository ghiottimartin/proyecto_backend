from jumbo_soft.signals import get_usuario_logueado
import locale
from rest_framework import serializers
from rest_framework.authtoken.views import Token
import secrets
from .models import Usuario, Rol, Producto, Categoria, Pedido, PedidoLinea

locale.setlocale(locale.LC_ALL, '')


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

    class Meta:
        model = Usuario
        fields = ['id', 'username', 'email', 'first_name', 'roles', 'habilitado', 'password', 'dni', 'operaciones',
                  'esAdmin', 'esMozo', 'esComensal', 'esVendedor']

    # Método que devuelve los datos del usuario. Quito la contraseña para que no sea mostrada al usuario.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['password'] = ""
        return ret

    # Método de creación de un usuario.
    def create(self, validated_data):
        user = Usuario.objects.create_user(**validated_data)
        user.token_email = secrets.token_hex(16)
        user.save()
        Token.objects.create(user=user)
        return user


class ProductoSerializer(CustomModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

    # Método que devuelve los datos del usuario. Quito la contraseña para que no sea mostrada al usuario.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['categoria_texto'] = instance.categoria.nombre
        ret['precio_texto'] = locale.currency(instance.precio_vigente)
        return ret


class CategoriaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categoria
        fields = '__all__'


class LineaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = PedidoLinea
        fields = ['id', 'cantidad', 'subtotal', 'producto', 'total']

    # Método que devuelve los datos de la línea.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['subtotal_texto'] = locale.currency(instance.subtotal)
        ret['total_texto'] = locale.currency(instance.total)
        return ret


class PedidoSerializer(serializers.ModelSerializer):
    lineas = LineaSerializer(many=True, read_only=True)
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = Pedido
        fields = '__all__'

    # Método que devuelve los datos del pedido.
    def to_representation(self, instance):
        logueado = get_usuario_logueado()

        ret = super().to_representation(instance)
        ret['id_texto'] = "P" + str(instance.id).zfill(5)
        ret['cancelado'] = instance.comprobar_estado_cancelado()
        ret['fecha_texto'] = instance.fecha.strftime('%d/%m/%Y %H:%M')
        ret['total_texto'] = locale.currency(instance.total)
        ret['estado_texto'] = instance.ultimo_estado.capitalize()
        ret['usuario_texto'] = instance.usuario.email
        ret['mostrar_usuario'] = logueado.esAdmin or logueado.esVendedor
        return ret

    def get_operaciones(self, objeto):
        logueado = get_usuario_logueado()
        operaciones = []

        puede_visualizar = objeto.comprobar_puede_visualizar(logueado)
        if puede_visualizar:
            accion = 'visualizar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-info text-info',
                'texto': 'Ver',
                'icono': 'fa fa-eye',
                'key': str(objeto.id) + "-" + accion,
            })

        puede_cerrar = objeto.comprobar_puede_cerrar(logueado)
        if puede_cerrar:
            accion = 'recibir'
            operaciones.append({
                'accion': 'recibir',
                'clase': 'btn btn-sm btn-success text-success',
                'texto': 'Entregar',
                'icono': 'fa fa-check-circle',
                'key': str(objeto.id) + "-" + accion,
            })

        puede_cancelar = objeto.comprobar_puede_cancelar(logueado)
        if puede_cancelar:
            accion = 'cancelar'
            operaciones.append({
                'accion': 'cancelar',
                'clase': 'btn btn-sm btn-danger text-danger',
                'texto': 'Cancelar',
                'icono': 'fa fa-window-close',
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones
