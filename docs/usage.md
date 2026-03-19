# Usage Guide

## Asset Tags and Naming

Every device gets a unique **asset tag** auto-generated from its category prefix and a sequential number. Use the asset tag in lab notebooks, measurement scripts, and setup documentation to identify the exact physical device.

| Category            | Prefix | Example tags          |
|---------------------|--------|-----------------------|
| Adapter             | ADP    | ADP-001, ADP-002, ... |
| Amplifier           | AMP    | AMP-001               |
| Antenna             | ANT    | ANT-001               |
| Attenuator          | ATT    | ATT-001, ATT-002, ... |
| Bias Tee            | BTE    | BTE-001               |
| Cable Assembly      | CBL    | CBL-001, CBL-002, ... |
| Circulator          | CIR    | CIR-001               |
| Connector           | CON    | CON-001               |
| Coupler             | CPL    | CPL-001               |
| DC Block            | DCB    | DCB-001               |
| Filter              | FLT    | FLT-001               |
| Frequency Reference | REF    | REF-001               |
| Mixer               | MIX    | MIX-001               |
| Power Divider       | DIV    | DIV-001               |
| Probe               | PRB    | PRB-001               |
| Switch              | SWT    | SWT-001               |
| Termination         | TRM    | TRM-001               |
| Waveguide           | WGD    | WGD-001               |
| Other               | OTH    | OTH-001               |

You can override the auto-generated tag when creating or editing a device if you have an existing numbering scheme. New categories can be added through the Django admin.

### What goes in the name vs. other fields

The **name** is a short, descriptive label to help you recognize the device at a glance. It doesn't need to be unique — the asset tag handles that. Avoid duplicating information that belongs in dedicated fields:

| Field | What to put there | Example |
|-------|-------------------|---------|
| **Name** | A recognizable shorthand | `355D Step Attenuator`, `12" SMA Cable (blue)` |
| **Manufacturer** | The maker | `HP`, `Mini-Circuits` |
| **Model Number** | Manufacturer's part/model number | `8495B`, `ZX60-P103LN+` |
| **Serial Number** | The unit's serial, if it has one | `MY12345678` |
| **Asset Tag** | Your lab's unique ID | `ATT-001` (auto-generated) |

For multiple identical units (e.g. three of the same SMA cable), the name can be the same — the asset tags (`CBL-001`, `CBL-002`, `CBL-003`) distinguish them. Adding a physical detail like cable color also helps: `12" SMA Cable (blue)`.

## Frequency Entry

Frequency fields accept values with k/M/G suffixes instead of typing out large numbers:

| Input | Stored as |
|-------|-----------|
| `2.4G` | 2,400,000,000 Hz |
| `100M` | 100,000,000 Hz |
| `10.7k` | 10,700 Hz |
| `1500` | 1,500 Hz |

You can also write `2.4 GHz`, `100MHz`, etc. — the parser is flexible. Values are stored internally in Hz and displayed with appropriate suffixes throughout the interface.

## Touchstone Files and Parameters

Upload Touchstone files (.s1p, .s2p, etc.) on a device's Touchstone tab. The file is parsed with scikit-rf on upload, and the metadata (port count, frequency range, impedance) is extracted automatically.

### Parameters

Touchstone files support arbitrary key-value **parameters** for documenting the device state at the time of measurement. This is essential for devices with multiple operating states:

- **Step attenuators** — `attenuation: 10 dB`, `attenuation: 20 dB`
- **Tunable filters** — `center_freq: 145 MHz`, `bandwidth: 10 MHz`
- **Switches** — `position: through`, `position: load`
- **Amplifiers** — `bias: 12V`, `gain_setting: high`

Parameters are entered as key/value pairs in the upload form. Use the "+ Add parameter" button for multiple parameters per file.

### Viewing S-Parameters

Click on any Touchstone file name to see its detail page, which shows the parsed metadata and an interactive plot rendered with Plotly.js. You can zoom, pan, and hover for exact values.

**Selecting traces** — The Plot Options panel lists every S-parameter in the file with a checkbox. Toggle individual traces on or off to focus on the parameters you care about. For a 2-port device this means you can, for example, show only S21 (forward transmission) without the clutter of S12, S11, and S22.

**Smith chart** — When the file contains reflection parameters (S11, S22, ...), a Smith Chart option appears under Chart Type. Switching to it plots the selected reflection parameters on a standard Smith chart, which is useful for inspecting impedance matching and return loss behaviour across frequency. Transmission parameters (S21, S12, ...) are not shown in Smith chart mode since they are not meaningful on a Smith chart.

## Documents

The Documents tab on each device can hold both uploaded files and external URLs. This covers datasheets, manuals, application notes, measurement results, and anything else you want to keep associated with a device.

### Document types

| Type | Typical use |
|------|-------------|
| Datasheet | Manufacturer's datasheet (PDF upload or link to manufacturer's site) |
| Manual | Operating or service manual |
| Application Note | Relevant app notes |
| Measurement | Non-Touchstone measurement data — spectrum screenshots, power meter logs, noise figure results, etc. |
| Other | Anything that doesn't fit the above |

### Files vs. URLs

When adding a document you can provide a **file**, a **URL**, or both:

- **File only** — upload a PDF, image, CSV, or any other file. It is stored on the server and served directly.
- **URL only** — link to an external resource (e.g. a manufacturer's datasheet page, a shared Google Drive file, a lab wiki page). Nothing is downloaded — the link is stored as-is.
- **Both** — useful when you have a local copy but also want to reference the canonical online source.

## Printing Labels

Each device detail page has a **Print Label** button that opens a print-ready page. The label contains:

- **QR code** linking to the device's page in the web interface
- **Asset tag** in large monospace font
- **Device name**, manufacturer/model, and serial number

### Setup for Brother QL-700

1. Install the Brother QL-700 printer driver for your OS.
2. Load 50mm continuous tape (DK-22225 or equivalent).
3. Click **Print Label** on any device detail page.
4. In the browser's print dialog:
   - Select the QL-700 as the printer.
   - Set paper size to **50mm** (or "DK22225" depending on your driver).
   - Set margins to **None** / **Minimum**.
   - Disable headers and footers.
5. Print.

The label is compact — asset tag and QR code are the primary elements so they stay readable even on small labels. You can also print to PDF for other label printers or manual cutting.

### Attaching labels to devices

- **Enclosures and instruments** — stick directly onto a flat surface.
- **Cables and small adapters** — apply the label to a plastic key tag (search AliExpress for "plastic key tags with ring 60x25mm") and attach with a zip tie. Alternatively, wrap the label flag-style around the cable near the connector — the adhesive sticks to itself.

## Python Client Library

The client library can be installed directly from GitHub on any machine on the lab network — no need to clone the full repo.

```bash
# Install from GitHub
uv pip install "lab-assets-client @ git+ssh://git@github.com/ErikOSorensen/lab_assets.git#subdirectory=client"

# Or with HTTPS
uv pip install "lab-assets-client @ git+https://github.com/ErikOSorensen/lab_assets.git#subdirectory=client"

# Or add to a project's dependencies (pyproject.toml)
uv add "lab-assets-client @ git+ssh://git@github.com/ErikOSorensen/lab_assets.git#subdirectory=client"
```

If you have a local clone of the repo, you can also install from that:

```bash
uv pip install -e client/
```

### Basic usage

```python
from lab_assets_client import LabAssetsClient

client = LabAssetsClient("http://lab-assets.local:8000", token="your-token")

# List all attenuators
devices = client.list_devices(category="attenuator")

# Get full device details
device = client.get_device(device_id)

# Get an skrf.Network from a specific Touchstone file
network = client.get_network(touchstone_id)
```

### Filtering by parameters

```python
# Get only the 10 dB setting for a step attenuator
nets = client.get_device_networks(device_id, attenuation="10 dB")

# Get all networks for a device
all_nets = client.get_device_networks(device_id)
```

### De-embedding example

A typical use case is de-embedding test cables and fixtures from a DUT measurement:

```python
# Retrieve fixture networks by asset tag
cable_in = client.get_device_networks(cable_in_id)[0]
cable_out = client.get_device_networks(cable_out_id)[0]

# De-embed
dut = cable_in.inv ** measured ** cable_out.inv
```

### Uploading Touchstone files

```python
# Upload with parameters
client.upload_touchstone(
    device_id,
    "hp355d_10dB.s2p",
    description="10 dB setting, measured 2026-03-13",
    parameters={"attenuation": "10 dB"},
)
```

### API token

Generate a token via the Django admin (/admin/ > Auth Token > Tokens) or:

```bash
# Docker deployment
docker compose exec web uv run python manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user = User.objects.get(username='admin')
token, _ = Token.objects.get_or_create(user=user)
print(token.key)
"
```
