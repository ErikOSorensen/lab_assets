from rest_framework import serializers
from devices.models import DeviceCategory, Device, DevicePhoto, Document, TouchstoneFile


class DeviceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceCategory
        fields = ['id', 'name', 'slug', 'description']


class DevicePhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevicePhoto
        fields = ['id', 'image', 'caption', 'is_primary', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'file', 'url', 'title', 'doc_type', 'uploaded_at']
        read_only_fields = ['id', 'uploaded_at']
        extra_kwargs = {'file': {'required': False}, 'url': {'required': False}}


class TouchstoneFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = TouchstoneFile
        fields = [
            'id', 'file', 'original_filename', 'description', 'parameters',
            'port_count', 'frequency_min_hz', 'frequency_max_hz',
            'frequency_npoints', 'impedance_ohms', 'uploaded_at',
        ]
        read_only_fields = [
            'id', 'original_filename', 'port_count', 'frequency_min_hz',
            'frequency_max_hz', 'frequency_npoints', 'impedance_ohms', 'uploaded_at',
        ]


class DeviceListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    primary_photo = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = [
            'id', 'asset_tag', 'name', 'category', 'category_name', 'manufacturer',
            'model_number', 'is_active', 'primary_photo',
        ]

    def get_primary_photo(self, obj):
        photo = obj.primary_photo
        if photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(photo.image.url)
            return photo.image.url
        return None


class DeviceDetailSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    photos = DevicePhotoSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    touchstone_files = TouchstoneFileSerializer(many=True, read_only=True)

    class Meta:
        model = Device
        fields = [
            'id', 'asset_tag', 'name', 'category', 'category_name', 'manufacturer',
            'model_number', 'serial_number', 'description',
            'frequency_min_hz', 'frequency_max_hz', 'port_count',
            'impedance_ohms', 'max_power_dbm', 'location', 'notes', 'is_active',
            'created_at', 'updated_at',
            'photos', 'documents', 'touchstone_files',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
