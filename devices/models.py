import uuid
from django.db import models


class DeviceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    prefix = models.CharField(max_length=10, unique=True, help_text="Short prefix for asset tags, e.g. ATT, MIX, CBL")
    description = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "device categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    asset_tag = models.CharField(max_length=20, unique=True, editable=True, blank=True,
                                 help_text="Auto-generated if left blank, e.g. ATT-001")
    name = models.CharField(max_length=200)
    category = models.ForeignKey(DeviceCategory, on_delete=models.PROTECT, related_name='devices')
    manufacturer = models.CharField(max_length=200, blank=True)
    model_number = models.CharField(max_length=200, blank=True)
    serial_number = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    frequency_min_hz = models.BigIntegerField(null=True, blank=True, help_text="Minimum frequency in Hz")
    frequency_max_hz = models.BigIntegerField(null=True, blank=True, help_text="Maximum frequency in Hz")
    port_count = models.PositiveIntegerField(null=True, blank=True)
    impedance_ohms = models.FloatField(null=True, blank=True, default=50.0)
    max_power_dbm = models.FloatField(null=True, blank=True, help_text="Maximum input power in dBm")
    location = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        parts = []
        if self.asset_tag:
            parts.append(f'[{self.asset_tag}]')
        parts.append(self.name)
        if self.manufacturer:
            parts.append(f"({self.manufacturer})")
        if self.model_number:
            parts.append(self.model_number)
        return ' '.join(parts)

    def save(self, *args, **kwargs):
        if not self.asset_tag:
            prefix = self.category.prefix
            last = (
                Device.objects.filter(asset_tag__startswith=f'{prefix}-')
                .order_by('-asset_tag')
                .values_list('asset_tag', flat=True)
                .first()
            )
            if last:
                try:
                    num = int(last.split('-', 1)[1]) + 1
                except (ValueError, IndexError):
                    num = 1
            else:
                num = 1
            self.asset_tag = f'{prefix}-{num:03d}'
        super().save(*args, **kwargs)

    @property
    def primary_photo(self):
        return self.photos.filter(is_primary=True).first() or self.photos.first()


def device_photo_path(instance, filename):
    return f"devices/{instance.device.id}/photos/{filename}"


def device_document_path(instance, filename):
    return f"devices/{instance.device.id}/documents/{filename}"


def device_touchstone_path(instance, filename):
    return f"devices/{instance.device.id}/touchstone/{filename}"


class DevicePhoto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to=device_photo_path)
    caption = models.CharField(max_length=300, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_primary', '-uploaded_at']

    def __str__(self):
        return self.caption or f"Photo of {self.device.name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            DevicePhoto.objects.filter(device=self.device, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Document(models.Model):
    DOC_TYPE_CHOICES = [
        ('datasheet', 'Datasheet'),
        ('manual', 'Manual'),
        ('app_note', 'Application Note'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to=device_document_path)
    title = models.CharField(max_length=300)
    doc_type = models.CharField(max_length=20, choices=DOC_TYPE_CHOICES, default='other')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['doc_type', 'title']

    def __str__(self):
        return self.title


class TouchstoneFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='touchstone_files')
    file = models.FileField(upload_to=device_touchstone_path)
    original_filename = models.CharField(max_length=300)
    description = models.CharField(max_length=500, blank=True)
    parameters = models.JSONField(default=dict, blank=True, help_text="Key-value parameters, e.g. {\"attenuation\": \"10 dB\"}")
    port_count = models.PositiveIntegerField(null=True, blank=True)
    frequency_min_hz = models.BigIntegerField(null=True, blank=True)
    frequency_max_hz = models.BigIntegerField(null=True, blank=True)
    frequency_npoints = models.PositiveIntegerField(null=True, blank=True)
    impedance_ohms = models.FloatField(null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']

    def __str__(self):
        return self.original_filename
