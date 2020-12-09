# Generated by Django 3.1.4 on 2020-12-15 14:08

from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ('stac_api', '0042_auto_20201215_1350'),
    ]

    operations = [
        migrations.AddField(
            model_name='asset',
            name='etag',
            field=models.CharField(
                default='23de8227-472d-4a29-b2e4-937133563b5d', editable=False, max_length=56
            ),
        ),
        migrations.AddField(
            model_name='collection',
            name='etag',
            field=models.CharField(
                default='aed99c07-6c35-4494-805f-10f11f2d7065', editable=False, max_length=56
            ),
        ),
        migrations.AddField(
            model_name='item',
            name='etag',
            field=models.CharField(
                default='83866729-f467-424f-94f1-f58d2b2cd12e', editable=False, max_length=56
            ),
        ),
    ]
