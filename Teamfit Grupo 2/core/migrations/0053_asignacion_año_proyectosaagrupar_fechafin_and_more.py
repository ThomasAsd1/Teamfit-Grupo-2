# Generated by Django 4.1.8 on 2024-10-04 18:38

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0052_alter_hh_estimado_detalle_semanal_fecha_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='asignacion',
            name='año',
            field=models.IntegerField(default=2024),
        ),
        migrations.AddField(
            model_name='proyectosaagrupar',
            name='fechaFin',
            field=models.DateField(blank=True, null=True, verbose_name='Fin del proyecto'),
        ),
        migrations.AddField(
            model_name='proyectosaagrupar',
            name='fechaInicio',
            field=models.DateField(blank=True, null=True, verbose_name='Inicio del proyecto'),
        ),
        migrations.AlterField(
            model_name='hh_estimado_detalle_semanal',
            name='fecha',
            field=models.DateTimeField(default=datetime.datetime(2024, 10, 4, 15, 38, 54, 218788), verbose_name='Fecha'),
        ),
    ]
