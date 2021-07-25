from django.contrib import admin
from .models import Usuario, Rol, Producto, Categoria, Pedido, PedidoLinea, Estado
from django.contrib.auth.admin import UserAdmin

admin.site.register(Usuario, UserAdmin)
admin.site.register(Rol)
admin.site.register(Producto)
admin.site.register(Categoria)
admin.site.register(Pedido)
admin.site.register(PedidoLinea)
admin.site.register(Estado)
