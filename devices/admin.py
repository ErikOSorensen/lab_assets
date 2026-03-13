from django.contrib import admin
from .models import DeviceCategory, Device, DevicePhoto, Document, TouchstoneFile


@admin.register(DeviceCategory)
class DeviceCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'prefix']
    prepopulated_fields = {'slug': ('name',)}


class DevicePhotoInline(admin.TabularInline):
    model = DevicePhoto
    extra = 1


class DocumentInline(admin.TabularInline):
    model = Document
    extra = 1


class TouchstoneFileInline(admin.TabularInline):
    model = TouchstoneFile
    extra = 1
    readonly_fields = ['port_count', 'frequency_min_hz', 'frequency_max_hz', 'frequency_npoints', 'impedance_ohms', 'parameters']


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ['asset_tag', 'name', 'category', 'manufacturer', 'model_number', 'max_power_dbm', 'is_active']
    list_filter = ['category', 'is_active', 'manufacturer']
    search_fields = ['asset_tag', 'name', 'manufacturer', 'model_number', 'serial_number']
    inlines = [DevicePhotoInline, DocumentInline, TouchstoneFileInline]


@admin.register(DevicePhoto)
class DevicePhotoAdmin(admin.ModelAdmin):
    list_display = ['device', 'caption', 'is_primary', 'uploaded_at']
    list_filter = ['is_primary']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'device', 'doc_type', 'uploaded_at']
    list_filter = ['doc_type']


@admin.register(TouchstoneFile)
class TouchstoneFileAdmin(admin.ModelAdmin):
    list_display = ['original_filename', 'device', 'port_count', 'frequency_npoints', 'uploaded_at']
