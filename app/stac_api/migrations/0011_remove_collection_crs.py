# Generated by Django 3.1.2 on 2020-11-04 08:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('stac_api', '0010_auto_20201104_0637'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='collection',
            name='crs',
        ),
    ]
