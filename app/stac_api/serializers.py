import logging
from collections import OrderedDict

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry

from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict
from rest_framework_gis import serializers as gis_serializers

from stac_api.models import Asset
from stac_api.models import Collection
from stac_api.models import CollectionLink
from stac_api.models import Item
from stac_api.models import ItemLink
from stac_api.models import Provider
from stac_api.models import get_default_stac_extensions
from stac_api.utils import isoformat

logger = logging.getLogger(__name__)


class NonNullModelSerializer(serializers.ModelSerializer):
    """Filter fields with null value

    Best practice is to not include (optional) fields whose
    value is None.
    """

    def to_representation(self, instance):

        def filter_null(obj):
            filtered_obj = {}
            if isinstance(obj, OrderedDict):
                filtered_obj = OrderedDict()
            for key, value in obj.items():
                if isinstance(value, dict):
                    filtered_obj[key] = filter_null(value)
                elif isinstance(value, list) and len(value) > 0:
                    filtered_obj[key] = value
                elif value is not None:
                    filtered_obj[key] = value
            return filtered_obj

        obj = super().to_representation(instance)
        return filter_null(obj)


class DictSerializer(serializers.ListSerializer):
    '''Represent objects within a dictionary instead of a list

    By default the Serializer with `many=True` attribute represent all objects within a list.
    Here we overwrite the ListSerializer to instead represent multiple objects using a dictionary
    where the object identifier is used as key.

    For example the following list:

        [{
                'name': 'object1',
                'description': 'This is object 1'
            }, {
                'name': 'object2',
                'description': 'This is object 2'
        }]

    Would be represented as follow:

        {
            'object1': {'description': 'This is object 1'},
            'object2': {'description': 'This is object 2'}
        }
    '''

    # pylint: disable=abstract-method

    key_identifier = 'name'

    def to_representation(self, data):
        objects = super().to_representation(data)
        return {obj.pop(self.key_identifier): obj for obj in objects}

    @property
    def data(self):
        ret = super(serializers.ListSerializer, self).data
        return ReturnDict(ret, serializer=self)


class ProviderSerializer(NonNullModelSerializer):

    class Meta:
        model = Provider
        fields = ['name', 'roles', 'url', 'description']


class ExtentTemporalSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    cache_start_datetime = serializers.DateTimeField()
    cache_end_datetime = serializers.DateTimeField()

    def to_representation(self, instance):
        ret = super().to_representation(instance)

        start = instance.cache_start_datetime
        end = instance.cache_end_datetime

        if start is not None:
            start = isoformat(start)

        if end is not None:
            end = isoformat(end)

        ret["temporal_extent"] = {"interval": [[start, end]]}

        return ret["temporal_extent"]


class ExtentSpatialSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    extent_geometry = gis_serializers.GeometryField

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        # handle empty field
        if instance.extent_geometry is None:
            ret["bbox"] = {"bbox": [[]]}
        else:
            bbox = GEOSGeometry(instance.extent_geometry).extent
            bbox = list(bbox)
            ret["bbox"] = {"bbox": [bbox]}
        return ret["bbox"]


class ExtentSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    spatial = ExtentSpatialSerializer(source="*")
    temporal = ExtentTemporalSerializer(source="*")


class CollectionLinkSerializer(NonNullModelSerializer):

    class Meta:
        model = CollectionLink
        fields = ['href', 'rel', 'link_type', 'title']


class CollectionSerializer(NonNullModelSerializer):

    class Meta:
        model = Collection
        fields = [
            'stac_version',
            'stac_extensions',
            'id',
            'title',
            'description',
            'summaries',
            'extent',
            'providers',
            'license',
            'created',
            'updated',
            'links',
            'crs',
            'itemType'
        ]
        # crs not in sample data, but in specs..

    crs = serializers.SerializerMethodField()
    created = serializers.DateTimeField(required=True)  # datetime
    updated = serializers.DateTimeField(required=True)  # datetime
    description = serializers.CharField(required=True)  # string
    extent = ExtentSerializer(read_only=True, source="*")
    summaries = serializers.JSONField(read_only=True)
    id = serializers.CharField(max_length=255, source="name")  # string
    license = serializers.CharField(max_length=30)  # string
    links = CollectionLinkSerializer(many=True, read_only=True)
    providers = ProviderSerializer(many=True)
    stac_extensions = serializers.SerializerMethodField()
    stac_version = serializers.SerializerMethodField()
    title = serializers.CharField(allow_blank=True, max_length=255)  # string
    itemType = serializers.ReadOnlyField(default="Feature")  # pylint: disable=invalid-name

    def get_crs(self, obj):
        return ["http://www.opengis.net/def/crs/OGC/1.3/CRS84"]

    def get_stac_extensions(self, obj):
        return get_default_stac_extensions()

    def get_stac_version(self, obj):
        return "0.9.0"

    def _update_or_create_providers(self, collection, providers_data):
        provider_ids = []
        for provider_data in providers_data:
            provider = Provider.objects.get_or_create(
                collection=collection,
                name=providers_data["name"],
                defaults={
                    'description': provider_data['description'],
                    'roles': provider_data['roles'],
                    'url': provider_data['url']
                }
            )
            provider_ids.append(provider.id)
            # the duplicate here is necessary to update the values in
            # case the object already exists
            provider.description = provider_data.get('description', provider.description)
            provider.roles = provider_data.get('roles', provider.roles)
            provider.url = provider_data.get('url', provider.url)

        # Delete providers that were not mentioned in the payload anymore
        deleted = Provider.objects.filter(collection=collection).exclude(id__in=provider_ids
                                                                        ).delete()
        logger.info(
            "deleted %d stale providers for collection %s",
            deleted[0],
            collection.name,
            extra={"collection": collection.name}
        )

    def create(self, validated_data):
        """
        Create and return a new `Collection` instance, given the validated data.
        """
        providers_data = validated_data.pop('providers', [])
        collection = Collection.objects.create(**validated_data)
        self._update_or_create_providers(collection=collection, providers_data=providers_data)
        return collection

    def update(self, instance, validated_data):
        """
        Update and return an existing `Collection` instance, given the validated data.
        """
        providers_data = validated_data.pop('providers', [])
        self._update_or_create_providers(collection=instance, providers_data=providers_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        name = instance.name
        api_base = settings.API_BASE
        request = self.context.get("request")
        representation = super().to_representation(instance)
        # Add auto links
        # We use OrderedDict, although it is not necessary, because the default serializer/model for
        # links already uses OrderedDict, this way we keep consistency between auto link and user
        # link
        representation['links'][:0] = [
            OrderedDict([
                ('rel', 'self'),
                ('href', request.build_absolute_uri(f'/{api_base}collections/{name}')),
            ]),
            OrderedDict([
                ('rel', 'root'),
                ('href', request.build_absolute_uri(f'/{api_base}')),
            ]),
            OrderedDict([
                ('rel', 'parent'),
                ('href', request.build_absolute_uri(f'/{api_base}collections')),
            ]),
            OrderedDict([
                ('rel', 'items'),
                ('href', request.build_absolute_uri(f'/{api_base}collections/{name}/items')),
            ])
        ]
        return representation


class ItemLinkSerializer(NonNullModelSerializer):

    class Meta:
        model = ItemLink
        fields = ['href', 'rel', 'link_type', 'title']


class ItemsPropertiesSerializer(serializers.Serializer):
    # pylint: disable=abstract-method
    # ItemsPropertiesSerializer is a nested serializer and don't directly create/write instances
    # therefore we don't need to implement the super method create() and update()
    datetime = serializers.DateTimeField(
        source='properties_datetime', allow_null=True, required=False
    )
    start_datetime = serializers.DateTimeField(
        source='properties_start_datetime', allow_null=True, required=False
    )
    end_datetime = serializers.DateTimeField(
        source='properties_end_datetime', allow_null=True, required=False
    )
    eo_gsd = serializers.FloatField(source='properties_eo_gsd', allow_null=True, read_only=True)
    title = serializers.CharField(required=True, source='properties_title', max_length=255)

    def get_fields(self):
        fields = super().get_fields()
        # This is a hack to allow fields with special characters
        fields['eo:gsd'] = fields.pop('eo_gsd')
        # logger.debug('Updated fields name: %s', fields)
        return fields


class BboxSerializer(gis_serializers.GeoFeatureModelSerializer):

    class Meta:
        model = Item
        geo_field = "geometry"
        auto_bbox = True
        fields = ['geometry']

    def to_representation(self, instance):
        python_native = super().to_representation(instance)
        return python_native['bbox']


class AssetsDictSerializer(DictSerializer):
    # pylint: disable=abstract-method
    key_identifier = 'asset_name'


class AssetSerializer(NonNullModelSerializer):
    type = serializers.CharField(source='media_type', max_length=200)
    eo_gsd = serializers.FloatField(source='eo_gsd')
    geoadmin_lang = serializers.CharField(source='geoadmin_lang', max_length=2)
    geoadmin_variant = serializers.CharField(source='geoadmin_variant', max_length=15)
    proj_epsg = serializers.IntegerField(source='proj_epsg')
    checksum_multihash = serializers.CharField(source='checksum_multihash', max_length=255)

    class Meta:
        model = Asset
        list_serializer_class = AssetsDictSerializer
        fields = [
            'asset_name',
            'title',
            'type',
            'href',
            'description',
            'eo_gsd',
            'geoadmin_lang',
            'geoadmin_variant',
            'proj_epsg',
            'checksum_multihash',
        ]

    def get_fields(self):
        fields = super().get_fields()
        # This is a hack to allow fields with special characters
        fields['eo:gsd'] = fields.pop('eo_gsd')
        fields['proj:epsg'] = fields.pop('proj_epsg')
        fields['geoadmin:variant'] = fields.pop('geoadmin_variant')
        fields['geoadmin:lang'] = fields.pop('geoadmin_lang')
        fields['checksum:multihash'] = fields.pop('checksum_multihash')
        logger.debug('Updated fields name: %s', fields)
        return fields


class ItemSerializer(NonNullModelSerializer):

    class Meta:
        model = Item
        fields = [
            'id',
            'collection',
            'type',
            'stac_version',
            'geometry',
            'bbox',
            'properties',
            'stac_extensions',
            'links',
            'assets',
        ]

    collection = serializers.StringRelatedField()
    id = serializers.CharField(source='name', required=True, max_length=255)
    properties = ItemsPropertiesSerializer(source='*')
    geometry = gis_serializers.GeometryField()
    # read only fields
    links = ItemLinkSerializer(many=True, read_only=True)
    type = serializers.ReadOnlyField(default='Feature')
    bbox = BboxSerializer(source='*', read_only=True)
    assets = AssetSerializer(many=True, read_only=True)
    stac_extensions = serializers.SerializerMethodField()
    stac_version = serializers.SerializerMethodField()

    def get_stac_extensions(self, obj):
        return get_default_stac_extensions()

    def get_stac_version(self, obj):
        return "0.9.0"

    def to_representation(self, instance):
        collection = instance.collection.name
        name = instance.name
        api = settings.API_BASE
        request = self.context.get("request")
        representation = super().to_representation(instance)
        # Add auto links
        # We use OrderedDict, although it is not necessary, because the default serializer/model for
        # links already uses OrderedDict, this way we keep consistency between auto link and user
        # link
        representation['links'][:0] = [
            OrderedDict([
                ('rel', 'self'),
                (
                    'href',
                    request.build_absolute_uri(f'/{api}collections/{collection}/items/{name}')
                ),
            ]),
            OrderedDict([
                ('rel', 'root'),
                ('href', request.build_absolute_uri(f'/{api}')),
            ]),
            OrderedDict([
                ('rel', 'parent'),
                ('href', request.build_absolute_uri(f'/{api}collections/{collection}/items')),
            ]),
            OrderedDict([
                ('rel', 'collection'),
                ('href', request.build_absolute_uri(f'/{api}collections/{collection}')),
            ])
        ]
        return representation
