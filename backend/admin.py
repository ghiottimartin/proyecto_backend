from django.contrib import admin
from .models import Usuario, Rol
from django.contrib.auth.admin import UserAdmin

admin.site.register(Usuario, UserAdmin)
admin.site.register(Rol)
