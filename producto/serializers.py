from base.serializers import CustomModelSerializer, UsuarioSerializer
from base.signals import get_usuario_logueado
from .models import Producto, Categoria, Ingreso, IngresoLinea, MovimientoStock, ReemplazoMercaderia, \
    ReemplazoMercaderiaLinea
from rest_framework import serializers

import locale

locale.setlocale(locale.LC_ALL, '')


class ProductoSerializer(CustomModelSerializer):
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = '__all__'

    # Método que devuelve los datos del producto
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['id_texto'] = instance.get_id_texto()
        ret['categoria_texto'] = instance.categoria.nombre
        ret['precio_texto'] = locale.currency(instance.precio_vigente)
        ret['costo_texto'] = locale.currency(instance.costo_vigente)
        ret['margen_texto'] = instance.get_margen_ganancia()
        ret['alertar'] = instance.comprobar_alerta_stock()
        return ret

    # Devuelve las operaciones disponibles para el producto actual.
    def get_operaciones(self, objeto):
        operaciones = []

        puede_tiene_movimientos = objeto.comprobar_tiene_movimientos()
        if puede_tiene_movimientos:
            accion = 'stock'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-primary text-primary btn',
                'texto': 'Stock',
                'icono': 'fas fa-boxes',
                'title': 'Ver Movimientos de stock del Producto ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        accion = 'editar'
        operaciones.append({
            'accion': accion,
            'clase': 'btn btn-sm btn-success text-success',
            'texto': 'Editar',
            'icono': 'fas fa-pencil-alt',
            'title': 'Editar Producto ' + objeto.get_id_texto(),
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
                'title': 'Borrar Producto ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones


class CategoriaSerializer(serializers.ModelSerializer):
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = Categoria
        fields = '__all__'

    # Método que devuelve los datos de la categoría del producto.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['id_texto'] = instance.get_id_texto()
        return ret

    # Devuelve las operaciones disponibles para la categoría actual.
    def get_operaciones(self, objeto):
        operaciones = []

        accion = 'editar'
        operaciones.append({
            'accion': accion,
            'clase': 'btn btn-sm btn-success text-success',
            'texto': 'Editar',
            'icono': 'fas fa-pencil-alt',
            'title': 'Editar Categoría ' + objeto.get_id_texto(),
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
                'title': 'Borrar Categoría ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones


class MovimientoSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)

    class Meta:
        model = MovimientoStock
        fields = '__all__'

    # Método que devuelve los datos del movimiento.
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id_texto'] = "M" + str(instance.id).zfill(5)
        ret['fecha_texto'] = instance.auditoria_creado_fecha.strftime('%d/%m/%Y %H:%M')
        ret['usuario_email'] = instance.auditoria_creador.email
        ret['usuario_nombre'] = instance.auditoria_creador.first_name
        return ret


class IngresoLineaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    movimientos = MovimientoSerializer(many=True, read_only=True)

    class Meta:
        model = IngresoLinea
        fields = ['id', 'cantidad', 'producto', 'costo', 'total', 'movimientos']

    # Método que devuelve los datos de la línea.
    def to_representation(self, instance):
        """Quito password"""
        ret = super().to_representation(instance)
        ret['costo_texto'] = locale.currency(instance.costo)
        ret['total_texto'] = locale.currency(instance.total)
        return ret


class IngresoSerializer(serializers.ModelSerializer):
    lineas = IngresoLineaSerializer(many=True, read_only=True)
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = Ingreso
        fields = '__all__'

    # Método que devuelve los datos del ingreso.
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id_texto'] = instance.get_id_texto()
        ret['usuario_email'] = instance.usuario.email
        ret['usuario_nombre'] = instance.usuario.first_name
        ret['fecha_texto'] = instance.fecha.strftime('%d/%m/%Y %H:%M')
        ret['total_texto'] = locale.currency(instance.total)
        ret['estado_texto'] = instance.get_estado_legible()
        ret['estado_clase'] = instance.get_estado_clase()
        ret['fecha_anulado'] = instance.get_fecha_anulado_texto()
        ret['anulado'] = instance.comprobar_anulado()
        return ret

    # Devuelve las operaciones disponibles para el ingreso actual.
    def get_operaciones(self, objeto):
        logueado = get_usuario_logueado()
        operaciones = []

        puede_tiene_movimientos = objeto.comprobar_tiene_movimientos()
        if puede_tiene_movimientos:
            accion = 'stock'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-primary text-primary btn',
                'texto': 'Stock',
                'icono': 'fas fa-boxes',
                'title': 'Ver Movimientos de stock del Ingreso ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        puede_visualizar = objeto.comprobar_puede_visualizar(logueado)
        if puede_visualizar:
            accion = 'visualizar'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-info text-info',
                'texto': 'Ver',
                'icono': 'fa fa-eye',
                'title': 'Ver Ingreso ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        puede_anular = objeto.comprobar_puede_anular(logueado)
        if False and puede_anular:
            accion = 'anular'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-danger text-danger',
                'texto': 'Anular',
                'icono': 'fa fa-window-close',
                'title': 'Anular Ingreso ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones


class ReemplazoMercaderiaLineaSerializer(serializers.ModelSerializer):
    producto = ProductoSerializer(read_only=True)
    movimientos = MovimientoSerializer(many=True, read_only=True)

    class Meta:
        model = ReemplazoMercaderiaLinea
        fields = '__all__'


class ReemplazoMercaderiaSerializer(serializers.ModelSerializer):
    lineas = ReemplazoMercaderiaLineaSerializer(many=True, read_only=True)
    operaciones = serializers.SerializerMethodField()

    class Meta:
        model = ReemplazoMercaderia
        fields = '__all__'

    # Método que devuelve los datos del ingreso.
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['id_texto'] = instance.get_id_texto()
        ret['usuario_email'] = instance.usuario.email
        ret['usuario_nombre'] = instance.usuario.first_name
        ret['fecha_texto'] = instance.fecha.strftime('%d/%m/%Y %H:%M')
        ret['estado_texto'] = instance.get_estado_legible()
        ret['estado_clase'] = instance.get_estado_clase()
        ret['fecha_anulado'] = instance.get_fecha_anulado_texto()
        ret['anulado'] = instance.comprobar_anulado()
        return ret

    # Devuelve las operaciones disponibles para el reemplazo de mercadería actual.
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
                'title': 'Ver Reemplazo ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })

        puede_anular = objeto.comprobar_puede_anular(logueado)
        if puede_anular:
            accion = 'anular'
            operaciones.append({
                'accion': accion,
                'clase': 'btn btn-sm btn-danger text-danger',
                'texto': 'Anular',
                'icono': 'fa fa-window-close',
                'title': 'Anular Reemplazo ' + objeto.get_id_texto(),
                'key': str(objeto.id) + "-" + accion,
            })
        return operaciones
