"""Python client for the RF Lab Asset Management API."""

import io
import tempfile
import os

import requests
import skrf


class LabAssetsClient:
    """Client for interacting with the RF Lab Assets REST API.

    Usage:
        client = LabAssetsClient("http://localhost:8000", token="your-token")
        devices = client.list_devices(category="attenuator")
        network = client.get_network(touchstone_id)
    """

    def __init__(self, base_url, token=None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if token:
            self.session.headers['Authorization'] = f'Token {token}'

    def _url(self, path):
        return f"{self.base_url}/api/v1/{path.lstrip('/')}"

    def _get(self, path, **params):
        resp = self.session.get(self._url(path), params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path, data=None, files=None):
        resp = self.session.post(self._url(path), data=data, files=files)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path):
        resp = self.session.delete(self._url(path))
        resp.raise_for_status()

    # --- Devices ---

    def list_devices(self, category=None, search=None, **kwargs):
        """List devices, optionally filtering by category slug or search query."""
        params = kwargs
        if category:
            params['category__slug'] = category
        if search:
            params['search'] = search
        return self._get('devices/', **params)

    def get_device(self, device_id):
        """Get full device details by UUID."""
        return self._get(f'devices/{device_id}/')

    # --- Touchstone ---

    def list_touchstone(self, device_id):
        """List Touchstone files for a device."""
        return self._get(f'devices/{device_id}/touchstone/')

    def upload_touchstone(self, device_id, file_path, description='', parameters=None):
        """Upload a Touchstone file to a device.

        Args:
            device_id: UUID of the device.
            file_path: Path to the .sNp file.
            description: Optional description string.
            parameters: Optional dict of key-value parameters,
                        e.g. {"attenuation": "10 dB"}.
        """
        import json
        data = {'description': description}
        if parameters:
            data['parameters'] = json.dumps(parameters)
        with open(file_path, 'rb') as f:
            return self._post(
                f'devices/{device_id}/touchstone/',
                data=data,
                files={'file': (os.path.basename(file_path), f)},
            )

    def get_network(self, touchstone_id):
        """Download S-parameter data and return an skrf.Network object."""
        data = self._get(f'touchstone/{touchstone_id}/network/')
        import numpy as np

        f = np.array(data['frequency_hz'])
        s_real = np.array(data['s_real'])
        s_imag = np.array(data['s_imag'])
        s = s_real + 1j * s_imag
        z0 = data['z0']

        freq = skrf.Frequency.from_f(f, unit='Hz')
        return skrf.Network(frequency=freq, s=s, z0=z0, name=data['filename'])

    def get_device_networks(self, device_id, **match_params):
        """Get Touchstone files for a device as skrf.Network objects.

        Args:
            device_id: UUID of the device.
            **match_params: Filter by parameter key-value pairs.
                e.g. get_device_networks(id, attenuation="10 dB")
                returns only networks whose parameters match.
        """
        ts_files = self.list_touchstone(device_id)
        networks = []
        for ts in ts_files:
            if match_params:
                params = ts.get('parameters', {})
                if not all(params.get(k) == v for k, v in match_params.items()):
                    continue
            net = self.get_network(ts['id'])
            networks.append(net)
        return networks

    def download_touchstone(self, touchstone_id, dest_path):
        """Download a raw Touchstone file to disk."""
        resp = self.session.get(self._url(f'touchstone/{touchstone_id}/download/'))
        resp.raise_for_status()
        with open(dest_path, 'wb') as f:
            f.write(resp.content)

    def delete_touchstone(self, touchstone_id):
        """Delete a Touchstone file."""
        self._delete(f'touchstone/{touchstone_id}/')

    # --- Photos ---

    def upload_photo(self, device_id, file_path, caption='', is_primary=False):
        """Upload a photo to a device."""
        with open(file_path, 'rb') as f:
            return self._post(
                f'devices/{device_id}/photos/',
                data={'caption': caption, 'is_primary': is_primary},
                files={'image': (os.path.basename(file_path), f)},
            )

    def delete_photo(self, photo_id):
        """Delete a photo."""
        self._delete(f'photos/{photo_id}/')

    # --- Documents ---

    def upload_document(self, device_id, file_path, title=None, doc_type='other'):
        """Upload a document to a device."""
        if title is None:
            title = os.path.basename(file_path)
        with open(file_path, 'rb') as f:
            return self._post(
                f'devices/{device_id}/documents/',
                data={'title': title, 'doc_type': doc_type},
                files={'file': (os.path.basename(file_path), f)},
            )

    def delete_document(self, doc_id):
        """Delete a document."""
        self._delete(f'documents/{doc_id}/')
