from django.db import migrations


CATEGORIES = [
    ('Attenuator', 'attenuator', 'ATT', 'Fixed and variable attenuators'),
    ('Mixer', 'mixer', 'MIX', 'Frequency mixers'),
    ('Cable Assembly', 'cable_assembly', 'CBL', 'Coaxial cable assemblies and test cables'),
    ('Coupler', 'coupler', 'CPL', 'Directional couplers and power dividers'),
    ('Amplifier', 'amplifier', 'AMP', 'Low-noise and power amplifiers'),
    ('Filter', 'filter', 'FLT', 'Bandpass, lowpass, highpass, and notch filters'),
    ('Antenna', 'antenna', 'ANT', 'Antennas and antenna accessories'),
    ('Connector', 'connector', 'CON', 'RF connectors and adapters'),
    ('Adapter', 'adapter', 'ADP', 'Coaxial adapters and transitions'),
    ('Bias Tee', 'bias_tee', 'BTE', 'Bias tees for injecting DC into RF paths'),
    ('DC Block', 'dc_block', 'DCB', 'DC blocking capacitors and assemblies'),
    ('Power Divider', 'power_divider', 'DIV', 'Power dividers and splitters'),
    ('Switch', 'switch', 'SWT', 'RF/coaxial switches, manual and electronic'),
    ('Termination', 'termination', 'TRM', 'Loads, terminations, and matched resistors'),
    ('Circulator', 'circulator', 'CIR', 'Circulators and isolators'),
    ('Frequency Reference', 'frequency_reference', 'REF', 'Oscillators, frequency standards, and references'),
    ('Waveguide', 'waveguide', 'WGD', 'Waveguide sections, transitions, and components'),
    ('Probe', 'probe', 'PRB', 'Near-field probes, current probes, and RF probes'),
    ('Other', 'other', 'OTH', 'Other RF/microwave components'),
]


def seed(apps, schema_editor):
    DeviceCategory = apps.get_model('devices', 'DeviceCategory')
    for name, slug, prefix, description in CATEGORIES:
        DeviceCategory.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'prefix': prefix, 'description': description},
        )


def unseed(apps, schema_editor):
    DeviceCategory = apps.get_model('devices', 'DeviceCategory')
    DeviceCategory.objects.filter(slug__in=[s for _, s, _, _ in CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
