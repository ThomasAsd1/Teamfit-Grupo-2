# Generated by Django 5.0.7 on 2024-08-01 21:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_alter_hh_estimado_detalle_semanal_fecha'),
    ]

    operations = [
        migrations.AlterField(
            model_name='hh_estimado_detalle_semanal',
            name='fecha',
            field=models.DateTimeField(default=datetime.datetime(2024, 8, 1, 17, 41, 1, 17541), verbose_name='Fecha'),
        ),
    ]
