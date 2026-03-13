from django.db import migrations


NEW_CATEGORIES = [
    ('Bias Tee', 'bias_tee', 'BTE', 'Bias tees for injecting DC into RF paths'),
    ('DC Block', 'dc_block', 'DCB', 'DC blocking capacitors and assemblies'),
    ('Power Divider', 'power_divider', 'DIV', 'Power dividers and splitters'),
    ('Switch', 'switch', 'SWT', 'RF/coaxial switches, manual and electronic'),
    ('Termination', 'termination', 'TRM', 'Loads, terminations, and matched resistors'),
    ('Circulator', 'circulator', 'CIR', 'Circulators and isolators'),
    ('Frequency Reference', 'frequency_reference', 'REF', 'Oscillators, frequency standards, and references'),
    ('Waveguide', 'waveguide', 'WGD', 'Waveguide sections, transitions, and components'),
    ('Probe', 'probe', 'PRB', 'Near-field probes, current probes, and RF probes'),
]


def seed(apps, schema_editor):
    DeviceCategory = apps.get_model('devices', 'DeviceCategory')
    for name, slug, prefix, description in NEW_CATEGORIES:
        DeviceCategory.objects.get_or_create(
            slug=slug,
            defaults={'name': name, 'prefix': prefix, 'description': description},
        )


def unseed(apps, schema_editor):
    DeviceCategory = apps.get_model('devices', 'DeviceCategory')
    DeviceCategory.objects.filter(slug__in=[s for _, s, _, _ in NEW_CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('devices', '0002_seed_categories'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
