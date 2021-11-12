# Generated by Django 3.2.4 on 2021-11-11 17:27

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('producto', '0007_movimientostock_venta_linea'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('mesas', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Turno',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('mesa', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='turnos', to='mesas.mesa')),
                ('mozo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('hora_inicio', models.DateTimeField(default=datetime.datetime.now)),
                ('hora_fin', models.DateTimeField(null=True)),
                ('auditoria_creado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('auditoria_modificado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('auditoria_creador', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('auditoria_modificado', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'mesas_turnos',
            },
        ),
        migrations.CreateModel(
            name='OrdenProducto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('turno', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ordenes', to='mesas.turno')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ordenes', to='producto.producto')),
                ('estado', models.CharField(default='solicitado', max_length=40)),
            ],
            options={
                'db_table': 'mesas_ordenes_productos',
            },
        ),
    ]
