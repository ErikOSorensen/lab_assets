import os
import tempfile
from dataclasses import dataclass

import skrf


@dataclass
class TouchstoneMetadata:
    port_count: int
    frequency_min_hz: float
    frequency_max_hz: float
    frequency_npoints: int
    impedance_ohms: float


def parse_touchstone(file_obj, filename):
    """Parse a Touchstone file and return metadata."""
    suffix = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        for chunk in file_obj.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        network = skrf.Network(tmp_path)
        return TouchstoneMetadata(
            port_count=network.number_of_ports,
            frequency_min_hz=float(network.f[0]),
            frequency_max_hz=float(network.f[-1]),
            frequency_npoints=len(network.f),
            impedance_ohms=float(network.z0[0, 0].real),
        )
    finally:
        os.unlink(tmp_path)


def generate_s_param_plot_data(file_path):
    """Generate S-parameter plot data for Plotly.js rendering.

    Returns magnitude (dB) traces for all parameters, plus real/imag
    data for reflection parameters (Sii) to support Smith chart display.
    """
    import numpy as np

    network = skrf.Network(file_path)
    freq_ghz = (network.f / 1e9).tolist()

    traces = []
    n_ports = network.number_of_ports
    for i in range(n_ports):
        for j in range(n_ports):
            s_complex = network.s[:, i, j]
            s_db = 20 * np.log10(np.abs(s_complex) + 1e-15)
            trace = {
                'name': f'S{i+1}{j+1}',
                'x': freq_ghz,
                'y': s_db.tolist(),
                'is_reflection': i == j,
            }
            if i == j:
                trace['real'] = s_complex.real.tolist()
                trace['imag'] = s_complex.imag.tolist()
            traces.append(trace)

    return {
        'frequencies_ghz': freq_ghz,
        'traces': traces,
        'title': os.path.basename(file_path),
    }
