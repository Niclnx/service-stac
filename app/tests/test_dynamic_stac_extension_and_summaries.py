import logging
from datetime import datetime

from django.conf import settings
from django.test import TestCase

from stac_api.models import Asset
from stac_api.models import Item
from stac_api.utils import utc_aware

import tests.database as db

logger = logging.getLogger(__name__)

API_BASE = settings.API_BASE


class DynamicStacExtensionsAndSummariesTestCase(TestCase):

    y100 = utc_aware(datetime.strptime('0100-01-01T00:00:00Z', '%Y-%m-%dT%H:%M:%SZ'))

    def setUp(self):
        self.collection = db.create_collection('collection-1')

    def add_item(self, name):
        item = Item.objects.create(
            collection=self.collection,
            name=name,
            properties_eo_gsd=None,
            properties_datetime=self.y100,
            properties_title="My title"
        )
        db.create_item_links(item)
        item.full_clean()
        item.save()
        self.collection.save()
        return item

    def create_asset(self, item, name, eo_gsd):
        asset = Asset.objects.create(
            item=item,
            title='my-title',
            name=name,
            checksum_multihash="01205c3fd6978a7d0b051efaa4263a09",
            description="this an asset",
            eo_gsd=eo_gsd,
            geoadmin_lang='fr',
            geoadmin_variant="kgrs",
            proj_epsg=2056,
            media_type="image/tiff; application=geotiff; profile=cloud-optimize",
            href=
            "https://data.geo.admin.ch/ch.swisstopo.pixelkarte-farbe-pk50.noscale/smr200-200-1-2019-2056-kgrs-10.tiff"
        )
        asset.full_clean()
        asset.save()
        item.save()
        return asset

    def test_collection_eo_gsd(self):

        # create an item
        i_1 = self.add_item("i1")

        # add different assets to the item
        b = self.create_asset(i_1, 'b', 4.4)
        a = self.create_asset(i_1, 'a', 3.4)
        # first adding the larger number and then the smaller number.
        # comparing it to [3.4, 4.4] to ensure, that the collection's
        # summaries["eo:gsd"] is sorted correctly.

        self.assertEqual(
            self.collection.summaries["eo:gsd"], [3.4],
            "Collection's eo_gsd was not updated correclty."
        )

        Asset.objects.get(pk=a.pk).delete()
        self.collection.refresh_from_db()

        self.assertEqual(
            self.collection.summaries["eo:gsd"],
            [4.4],
            "Collection's eo_gsd was not updated correclty after asset was deleted."
        )

    # further tests should have been developed, but then it was decided to set stac_extensions to [] for collections ant items
    # as well as to drop information on eo- and geoadmin-extensions from items.
    