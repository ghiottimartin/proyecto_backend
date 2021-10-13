# Generated by Django 3.2.4 on 2021-10-13 19:44

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('producto', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='costo_vigente',
            field=models.FloatField(default=0),
            preserve_default=False,
        ),
        migrations.CreateModel(
            name='Costo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auditoria_creado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('auditoria_modificado_fecha', models.DateTimeField(blank=True, default=datetime.datetime.now)),
                ('fecha', models.DateTimeField(default=datetime.datetime.now)),
                ('costo', models.FloatField()),
                ('auditoria_creador', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('auditoria_modificado', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('producto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='costos', to='producto.producto')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
