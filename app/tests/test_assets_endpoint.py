import logging
from json import dumps
from json import loads
from pprint import pformat

from django.conf import settings
from django.test import Client
from django.test import TestCase

from stac_api.serializers import AssetSerializer

import tests.database as db

logger = logging.getLogger(__name__)

API_BASE = settings.API_BASE


def to_dict(input_ordered_dict):
    return loads(dumps(input_ordered_dict))


class AssetsEndpointTestCase(TestCase):

    def setUp(self):
        self.client = Client()
        self.collections, self.items, self.assets = db.create_dummy_db_content(4, 4, 2)
        self.maxDiff = None  # pylint: disable=invalid-name

    def test_assets_endpoint(self):
        collection_name = self.collections[0].collection_name
        item_name = self.items[0][0].item_name
        response = self.client.get(
            f"/{API_BASE}collections/{collection_name}/items/{item_name}/assets?format=json"
        )
        self.assertEqual(200, response.status_code)
        json_data = response.json()
        logger.debug('Response (%s):\n%s', type(json_data), pformat(json_data))

        # Check that the answer is equal to the initial data
        serializer = AssetSerializer(self.assets[0][0], many=True)
        original_data = to_dict(serializer.data)
        original_data.update({
            'links': [{
                'rel': 'next',
                'href':
                    'http://testserver/api/stac/v0.9/collections/collection-1/items/item-1-1/assets?cursor=cD0y&format=json'
            }]
        })
        logger.debug('Serialized data:\n%s', pformat(original_data))
        self.assertDictEqual(
            original_data, json_data, msg="Returned data does not match expected data"
        )

    def test_single_asset_endpoint(self):
        collection_name = self.collections[0].collection_name
        item_name = self.items[0][0].item_name
        asset_name = self.assets[0][0][0].asset_name
        response = self.client.get(
            f"/{API_BASE}collections/{collection_name}/items/{item_name}"
            f"/assets/{asset_name}?format=json"
        )
        self.assertEqual(200, response.status_code)
        json_data = response.json()
        logger.debug('Response (%s):\n%s', type(json_data), pformat(json_data))

        # Check that the answer is equal to the initial data
        serializer = AssetSerializer(self.assets[0][0][0])
        original_data = to_dict(serializer.data)
        logger.debug('Serialized data:\n%s', pformat(original_data))
        self.assertDictEqual(
            original_data, json_data, msg="Returned data does not match expected data"
        )
