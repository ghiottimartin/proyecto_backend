# Generated by Django 3.1.7 on 2021-06-05 18:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0002_auto_20210605_1451'),
    ]

    operations = [
        migrations.CreateModel(
            name='Rol',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=50)),
                ('legible', models.CharField(max_length=50)),
                ('descripcion', models.CharField(max_length=250)),
                ('root', models.BooleanField(default=False)),
            ],
        ),
        migrations.AddField(
            model_name='usuario',
            name='roles',
            field=models.ManyToManyField(blank=True, related_name='usuarios_roles', to='backend.Rol'),
        ),
    ]