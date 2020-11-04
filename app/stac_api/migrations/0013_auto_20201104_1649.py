# Generated by Django 3.1.2 on 2020-11-04 16:49

from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.geos import MultiPolygon
from django.contrib.gis.geos import Polygon
from django.contrib.gis.geos.prototypes.io import wkt_w
from django.db import migrations


# Forwares
def convert_multipolygons_to_polygons(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    Item = apps.get_model('stac_api', 'Item')
    for item in Item.objects.all():
        wkt = wkt_w(dim=2).write(item.geometry_old.convex_hull).decode()
        item.geometry = GEOSGeometry(wkt, srid=2056)
        item.save()


# Backwards
def convert_polygons_to_multipolygons(apps, schema_editor):
    # We can't import the Person model directly as it may be a newer
    # version than this migration expects. We use the historical version.
    # We omit the backwards way, effort too big since we don't have data yet
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('stac_api', '0012_auto_20201104_1647'),
    ]

    # see https://docs.djangoproject.com/en/3.1/ref/migration-operations/#runpython
    # for reference
    operations = [
        migrations.RunPython(convert_multipolygons_to_polygons, convert_polygons_to_multipolygons),
    ]
