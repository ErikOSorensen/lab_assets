# RF Lab Asset Management System

A Django web application for managing home electronics/RF lab devices — attenuators, mixers, cable assemblies, couplers, and more. Upload Touchstone files (.sNp), device photos, and datasheets. View S-parameter plots in the browser. Use the Python client library to pull `skrf.Network` objects directly into measurement scripts for de-embedding.

## Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

## Fresh Install

```bash
# Clone the repo
git clone <repo-url>
cd lab_assets

# Install dependencies
uv sync

# Run database migrations
uv run python manage.py migrate

# Create an admin account
uv run python manage.py createsuperuser

# Start the development server
uv run python manage.py runserver
```

The app will be available at http://localhost:8000. The Django admin is at http://localhost:8000/admin/.

Ten default device categories (Attenuator, Mixer, Cable Assembly, etc.) are created automatically during migration.

## API Token Setup

To use the REST API or the Python client with token authentication, generate a token in the Django admin under **Auth Token > Tokens**, or run:

```bash
uv run python manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user = User.objects.get(username='your_username')
token, _ = Token.objects.get_or_create(user=user)
print(token.key)
"
```

The REST API is at http://localhost:8000/api/v1/.

## Python Client Library

The `client/` directory contains a standalone pip-installable package for scripting against the API.

```bash
# Install the client (from the repo root)
pip install -e client/
```

Usage:

```python
from lab_assets_client import LabAssetsClient

client = LabAssetsClient("http://localhost:8000", token="your-token")

# List devices
devices = client.list_devices(category="attenuator")

# Get an skrf.Network object from a Touchstone file
network = client.get_network(touchstone_id="<uuid>")

# De-embed fixtures
dut = cable_in.inv ** measured ** cable_out.inv
```

## Asset Tags and Naming

Every device gets a unique **asset tag** that is auto-generated from the category prefix and a sequential number:

| Category       | Prefix | Example tags           |
|----------------|--------|------------------------|
| Attenuator     | ATT    | ATT-001, ATT-002, ...  |
| Mixer          | MIX    | MIX-001, MIX-002, ...  |
| Cable Assembly | CBL    | CBL-001, CBL-002, ...  |
| Coupler        | CPL    | CPL-001                |
| Amplifier      | AMP    | AMP-001                |
| Filter         | FLT    | FLT-001                |
| Antenna        | ANT    | ANT-001                |
| Connector      | CON    | CON-001                |
| Adapter        | ADP    | ADP-001                |
| Other          | OTH    | OTH-001                |

The asset tag is the stable, human-readable identifier you should use in lab notebooks, measurement scripts, and setup documentation. You can override the auto-generated tag when creating or editing a device if you have an existing numbering scheme.

### What goes in the name vs. other fields

The **name** field is a short, descriptive label to help you recognize the device at a glance. It does not need to be unique — the asset tag handles that. Keep names concise and avoid duplicating information that belongs in dedicated fields:

| Field | What to put there | Example |
|-------|-------------------|---------|
| **Name** | A recognizable shorthand for *this particular device* | `355D Step Attenuator`, `12" SMA Cable (blue)` |
| **Manufacturer** | The maker | `HP`, `Mini-Circuits` |
| **Model Number** | The manufacturer's part/model number | `8495B`, `ZX60-P103LN+` |
| **Serial Number** | The unit's serial number, if it has one | `MY12345678` |
| **Asset Tag** | Auto-generated unique ID for your lab | `ATT-001` (auto) |

For devices where you have multiple identical units (e.g. three of the same SMA cable), the name can be the same for all of them — the asset tag (`CBL-001`, `CBL-002`, `CBL-003`) distinguishes them. Adding a physical detail to the name (like a cable color) can also help: `12" SMA Cable (blue)`, `12" SMA Cable (red)`.

## Printing Labels

Each device detail page has a **Print Label** button that opens a print-ready page sized for a Brother QL-700 (62mm continuous tape). The label contains:

- **QR code** linking to the device's page in the web interface
- **Asset tag** in large monospace font
- **Device name**, manufacturer/model, and serial number

### Setup for Brother QL-700

1. Install the Brother QL-700 printer driver for your OS.
2. Load 62mm continuous tape (DK-22205 or equivalent).
3. Click **Print Label** on any device detail page.
4. In the browser's print dialog:
   - Select the QL-700 as the printer.
   - Set paper size to **62mm** (or "DC22205" depending on your driver).
   - Set margins to **None** / **Minimum**.
   - Disable headers and footers.
5. Print.

The label is designed to be compact — asset tag and QR code are the primary elements so they remain readable on small labels. You can also print to PDF for other label printers or manual cutting.

## Frequency Entry

Frequency fields accept values with k/M/G suffixes:

| Input | Stored as |
|-------|-----------|
| `2.4G` | 2,400,000,000 Hz |
| `100M` | 100,000,000 Hz |
| `10.7k` | 10,700 Hz |
| `1500` | 1,500 Hz |

## Project Layout

```
lab_assets/          Django project settings and root URL config
devices/             Main app — models, views, templates, Touchstone parsing
api/                 REST API — DRF serializers, viewsets, routing
client/              Standalone Python client library
media/               Uploaded files (gitignored)
```
