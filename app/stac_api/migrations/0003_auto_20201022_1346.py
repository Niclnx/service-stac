# pylint: disable=C0301
# Generated by Django 3.1 on 2020-10-22 13:46

import django.contrib.gis.db.models.fields
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stac_api', '0002_auto_20201016_1423'),
    ]

    operations = [
        migrations.RenameField(
            model_name='collection',
            old_name='northeast',
            new_name='extent',
        ),
        migrations.RemoveField(
            model_name='collection',
            name='southwest',
        ),
        migrations.RemoveField(
            model_name='item',
            name='GeoJSON_type',
        ),
        migrations.RemoveField(
            model_name='item',
            name='geometry_coordinates',
        ),
        migrations.RemoveField(
            model_name='item',
            name='geometry_type',
        ),
        migrations.RemoveField(
            model_name='item',
            name='northeast',
        ),
        migrations.RemoveField(
            model_name='item',
            name='southwest',
        ),
        migrations.AddField(
            model_name='item',
            name='geometry',
            field=django.contrib.gis.db.models.fields.MultiPolygonField(
                default=
                'SRID=2056;MULTIPOLYGON(((2317000 913000 0,3057000 913000 0,3057000 1413000 0,2317000 1413000 0,2317000 913000 0)))',
                dim=3,
                srid=2056
            ),
        ),
    ]
