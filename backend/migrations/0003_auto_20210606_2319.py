# Generated by Django 3.2.4 on 2021-06-07 02:19

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_auto_20210606_2316'),
    ]

    operations = [
        migrations.RenameField(
            model_name='usuario',
            old_name='auditoria_creador_id',
            new_name='auditoria_creador',
        ),
        migrations.RemoveField(
            model_name='usuario',
            name='auditoria_creado',
        ),
        migrations.RemoveField(
            model_name='usuario',
            name='auditoria_modificado_id',
        ),
        migrations.AddField(
            model_name='usuario',
            name='auditoria_creado_fecha',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 6, 6, 23, 19, 56, 393591)),
        ),
        migrations.AddField(
            model_name='usuario',
            name='auditoria_modificado_fecha',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2021, 6, 6, 23, 19, 56, 393591)),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='auditoria_modificado',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
    ]
