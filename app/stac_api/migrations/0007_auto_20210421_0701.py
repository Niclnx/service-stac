# Generated by Django 3.1.7 on 2021-04-21 07:01

import django.db.models.deletion
from django.db import migrations
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ('stac_api', '0006_auto_20210419_1409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='asset',
            name='item',
            field=models.ForeignKey(
                help_text=
                '\n    <div class=SearchUsage>\n        Search Usage:\n        <ul>\n            <li>\n                <i>arg</i> will make a non exact search checking if <i>>arg</i>\n                is part of the Item path\n            </li>\n            <li>\n                Multiple <i>arg</i>  can be used, separated by spaces. This will search\n                for all elements containing all arguments in their path\n            </li>\n            <li>\n                <i>"collectionID/itemID"</i> will make an exact search for the specified item.\n             </li>\n        </ul>\n        Examples :\n        <ul>\n            <li>\n                Searching for <i>pixelkarte</i> will return all items which have\n                pixelkarte as a part of either their collection ID or their item ID\n            </li>\n            <li>\n                Searching for <i>pixelkarte 2016 4</i> will return all items\n                which have pixelkarte, 2016 AND 4 as part of their collection ID or\n                item ID\n            </li>\n            <li>\n                Searching for <i>"ch.swisstopo.pixelkarte.example/item2016-4-example"</i>\n                will yield only this item, if this item exists.\n            </li>\n        </ul>\n    </div>',
                on_delete=django.db.models.deletion.PROTECT,
                related_name='assets',
                related_query_name='asset',
                to='stac_api.item'
            ),
        ),
    ]
