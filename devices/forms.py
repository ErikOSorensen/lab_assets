import re

from django import forms
from .models import Device, DevicePhoto, Document, TouchstoneFile


SUFFIX_MULTIPLIERS = {
    'k': 1e3,
    'M': 1e6,
    'G': 1e9,
}

# Pattern: optional number (int or decimal), optional whitespace, optional suffix
_FREQ_RE = re.compile(
    r'^\s*([0-9]+(?:\.[0-9]*)?)\s*([kMG])?(?:Hz)?\s*$'
)


def _hz_to_suffixed(value_hz):
    """Convert a value in Hz to a compact suffixed string (e.g. 2.4G, 100M)."""
    if value_hz is None:
        return ''
    value_hz = float(value_hz)
    for suffix, mult in [('G', 1e9), ('M', 1e6), ('k', 1e3)]:
        if value_hz >= mult and value_hz % mult == 0:
            # Exact integer in this unit
            return f'{int(value_hz / mult)}{suffix}'
        if value_hz >= mult:
            formatted = f'{value_hz / mult:.6f}'.rstrip('0').rstrip('.')
            return f'{formatted}{suffix}'
    return str(int(value_hz)) if value_hz == int(value_hz) else str(value_hz)


class FrequencyField(forms.CharField):
    """A form field that accepts frequencies with k/M/G suffixes.

    Accepts values like: 2.4G, 100M, 10.7k, 1500, 2400MHz, 5.8 GHz
    Stores and returns the value in Hz as an integer.
    """

    def __init__(self, **kwargs):
        kwargs.setdefault('help_text', 'e.g. 2.4G, 100M, 10.7k, or value in Hz')
        super().__init__(**kwargs)

    def prepare_value(self, value):
        """Display stored Hz value with a human-friendly suffix."""
        if value is None or value == '':
            return ''
        # If it's already a string with a suffix (user just typed it), pass through
        if isinstance(value, str) and not value.strip().isdigit():
            return value
        return _hz_to_suffixed(value)

    def clean(self, value):
        value = super().clean(value)
        if not value:
            return None

        m = _FREQ_RE.match(value)
        if not m:
            raise forms.ValidationError(
                'Enter a frequency like 2.4G, 100M, 10.7k, or a plain number in Hz.'
            )

        number = float(m.group(1))
        suffix = m.group(2)
        if suffix:
            number *= SUFFIX_MULTIPLIERS[suffix]

        return int(round(number))


class BootstrapFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.setdefault('class', 'form-check-input')
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.setdefault('class', 'form-select')
            elif isinstance(field.widget, forms.FileInput):
                field.widget.attrs.setdefault('class', 'form-control')
            else:
                field.widget.attrs.setdefault('class', 'form-control')


class DeviceForm(BootstrapFormMixin, forms.ModelForm):
    frequency_min_hz = FrequencyField(required=False, label='Frequency Min')
    frequency_max_hz = FrequencyField(required=False, label='Frequency Max')

    class Meta:
        model = Device
        fields = [
            'asset_tag', 'name', 'category', 'manufacturer', 'model_number', 'serial_number',
            'description', 'frequency_min_hz', 'frequency_max_hz', 'port_count',
            'impedance_ohms', 'max_power_dbm', 'location', 'notes', 'is_active',
        ]
        help_texts = {
            'asset_tag': 'Leave blank to auto-generate (e.g. ATT-001)',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class DevicePhotoForm(forms.ModelForm):
    class Meta:
        model = DevicePhoto
        fields = ['image', 'caption', 'is_primary']


class DocumentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file', 'url', 'title', 'doc_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['file'].required = False
        self.fields['url'].required = False

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('file') and not cleaned.get('url'):
            raise forms.ValidationError('Provide either a file or a URL (or both).')
        return cleaned


class TouchstoneUploadForm(forms.ModelForm):
    param_keys = forms.CharField(required=False, widget=forms.HiddenInput())
    param_values = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = TouchstoneFile
        fields = ['file', 'description']

    def clean(self):
        cleaned = super().clean()
        # Parameters are submitted as parallel lists from the JS-driven form rows
        # But for the simple inline form, they come as getlist() — handled in the view
        return cleaned
