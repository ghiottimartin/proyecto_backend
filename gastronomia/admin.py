from django.contrib import admin
from .models import Pedido, PedidoLinea, Estado


admin.site.register(Pedido)
admin.site.register(PedidoLinea)
admin.site.register(Estado)
