from django import template

register = template.Library()


@register.filter
def format_frequency(value_hz):
    """Format a frequency in Hz to a human-readable string."""
    if value_hz is None:
        return ''
    value_hz = float(value_hz)
    for unit, divisor in [('GHz', 1e9), ('MHz', 1e6), ('kHz', 1e3)]:
        if value_hz >= divisor:
            formatted = f'{value_hz / divisor:.6f}'.rstrip('0').rstrip('.')
            return f'{formatted} {unit}'
    return f'{value_hz:g} Hz'


@register.filter
def file_extension(value):
    """Return the file extension."""
    if value:
        import os
        return os.path.splitext(str(value))[1].lower()
    return ''
