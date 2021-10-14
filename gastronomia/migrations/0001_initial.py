# Generated by Django 3.2.4 on 2021-10-13 23:06

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('producto', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Pedido',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auditoria_creado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('auditoria_modificado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('fecha', models.DateTimeField(default=datetime.datetime.now)),
                ('ultimo_estado', models.CharField(default='abierto', max_length=40)),
                ('total', models.FloatField()),
                ('forzar', models.BooleanField(default=False)),
                ('tipo', models.CharField(max_length=15)),
                ('auditoria_creador', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('auditoria_modificado', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('usuario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PedidoLinea',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('cantidad', models.IntegerField()),
                ('subtotal', models.FloatField()),
                ('total', models.FloatField()),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lineas', to='gastronomia.pedido')),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='+', to='producto.producto')),
            ],
        ),
        migrations.CreateModel(
            name='Estado',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('estado', models.CharField(max_length=40)),
                ('fecha', models.DateTimeField(default=datetime.datetime.now)),
                ('pedido', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='estados', to='gastronomia.pedido')),
            ],
        ),
    ]
