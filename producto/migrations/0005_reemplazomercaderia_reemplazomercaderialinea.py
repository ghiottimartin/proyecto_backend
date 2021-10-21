# Generated by Django 3.2.4 on 2021-10-21 18:46

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('producto', '0004_alta_ingresos'),
    ]

    operations = [
        migrations.CreateModel(
            name='ReemplazoMercaderia',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reemplazos', to=settings.AUTH_USER_MODEL)),
                ('fecha', models.DateTimeField(default=datetime.datetime.now)),
                ('anulado', models.DateTimeField(null=True)),
                ('auditoria_creado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('auditoria_modificado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('auditoria_creador', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('auditoria_modificado', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ReemplazoMercaderiaLinea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reemplazo', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lineas', to='producto.reemplazomercaderia')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='reemplazos', to='producto.producto')),
                ('stock_anterior', models.IntegerField()),
                ('stock_nuevo', models.IntegerField()),
                ('reemplazo_completo', models.BooleanField(default=False)),
            ],
        ),
    ]
