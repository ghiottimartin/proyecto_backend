# Generated by Django 3.2.4 on 2021-06-08 23:22

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('base', '0004_auto_20210608_2239'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usuario',
            name='auditoria_creado_fecha',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now),
        ),
        migrations.AlterField(
            model_name='usuario',
            name='auditoria_modificado_fecha',
            field=models.DateTimeField(blank=True, default=datetime.datetime.now),
        ),
    ]