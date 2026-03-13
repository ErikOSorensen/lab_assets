# RF Lab Asset Management System

A Django web application for managing home electronics/RF lab devices — attenuators, mixers, cable assemblies, couplers, and more. Upload Touchstone files (.sNp), device photos, and datasheets. View S-parameter plots in the browser. Use the Python client library to pull `skrf.Network` objects directly into measurement scripts for de-embedding.

## Deployment

The app is designed to run as a Docker Compose stack, typically inside a Proxmox LXC container on the lab network. The stack includes the Django app (served by gunicorn) and a PostgreSQL database.

### Prerequisites

- A Proxmox LXC container (or any Linux host) with Docker and Docker Compose installed
- Git

If your LXC doesn't have Docker yet:

```bash
apt-get update && apt-get install -y docker.io docker-compose-v2 git
```

### Installation

```bash
git clone <repo-url>
cd lab_assets
cp .env.example .env    # then edit .env — see below
docker compose up -d
```

On first start, the entrypoint automatically:
1. Waits for PostgreSQL to be ready
2. Runs all database migrations
3. Seeds the 19 default device categories
4. Creates the admin superuser

The app will be available at `http://<your-host>:8000`.

### Configuration (.env)

Copy `.env.example` and edit it:

```env
# REQUIRED: Generate a real key with:
#   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=your-secret-key-here

# Admin account (created on first start)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=changeme
DJANGO_SUPERUSER_EMAIL=you@example.com

# Hostnames/IPs that can access the app — include your LXC's IP
# and any hostname you use to reach it from the lab network
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,lab-assets.local,192.168.1.50

# Required if accessing via hostname:port (one entry per origin)
DJANGO_CSRF_TRUSTED_ORIGINS=http://lab-assets.local:8000,http://192.168.1.50:8000

# Database password (only used internally between containers)
POSTGRES_PASSWORD=change-this-too

# Port exposed on the host (default 8000)
WEB_PORT=8000
```

### Accessing from the lab network

After starting the stack, the app is reachable at `http://<lxc-ip>:8000` from any machine on the same network. If you have local DNS (e.g. from your router or a Pi-hole), point a hostname like `lab-assets.local` at the LXC's IP for convenience.

Make sure `DJANGO_ALLOWED_HOSTS` includes every hostname and IP you'll use in the browser, and `DJANGO_CSRF_TRUSTED_ORIGINS` includes the full origin (with `http://` and port) for each.

### Updates

```bash
cd lab_assets
git pull
docker compose up -d --build
```

The entrypoint re-runs migrations automatically, so schema changes from new versions are applied on restart.

### Managing the stack

```bash
docker compose up -d          # Start in background
docker compose logs -f web    # Follow app logs
docker compose restart web    # Restart after config changes
docker compose down           # Stop everything
docker compose down -v        # Stop and delete all data (destructive!)
```

### Backups

Database and uploaded files live in Docker volumes. Back them up regularly — a cron job running the database dump daily is a good idea.

```bash
# Database dump
docker compose exec db pg_dump -U lab_assets lab_assets > backup_$(date +%F).sql

# Restore a database dump
docker compose exec -T db psql -U lab_assets lab_assets < backup_2026-03-13.sql

# Back up uploaded files (photos, documents, Touchstone files)
docker compose cp web:/app/media ./media-backup

# Restore media files
docker compose cp ./media-backup/. web:/app/media
```

### Starting on boot

If your LXC or host uses systemd, Docker containers with `restart: unless-stopped` will come back after a reboot as long as the Docker daemon starts. Add this to the compose file or just ensure Docker is enabled:

```bash
systemctl enable docker
```

## Local Development (without Docker)

For development you can run directly with SQLite — no Docker or PostgreSQL needed.

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

### Setup

```bash
git clone <repo-url>
cd lab_assets
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

The app will be at http://localhost:8000. When no `DATABASE_URL` environment variable is set, it uses SQLite automatically.

## API Token Setup

To use the REST API or the Python client library with token authentication, generate a token via the Django admin (/admin/ > Auth Token > Tokens) or from the command line:

```bash
# Docker
docker compose exec web uv run python manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user = User.objects.get(username='admin')
token, _ = Token.objects.get_or_create(user=user)
print(token.key)
"

# Local development
uv run python manage.py shell -c "
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
user = User.objects.get(username='admin')
token, _ = Token.objects.get_or_create(user=user)
print(token.key)
"
```

The REST API is at `http://<your-host>:8000/api/v1/`.

## Python Client Library

The `client/` directory contains a standalone pip-installable package for use in measurement scripts and Jupyter notebooks on your lab machines.

```bash
pip install -e client/
```

Usage:

```python
from lab_assets_client import LabAssetsClient

client = LabAssetsClient("http://lab-assets.local:8000", token="your-token")

# List devices
devices = client.list_devices(category="attenuator")

# Get an skrf.Network from a Touchstone file
network = client.get_network(touchstone_id="<uuid>")

# Retrieve a specific attenuator setting
nets = client.get_device_networks(device_id, attenuation="10 dB")

# De-embed fixtures from a measurement
dut = cable_in.inv ** measured ** cable_out.inv
```

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

For cables and small adapters without a flat surface, you can apply the label to a plastic key tag (search "plastic key tags with ring 60x25mm") and attach it with a zip tie, or wrap the label flag-style around the cable near the connector.

## Frequency Entry

Frequency fields accept values with k/M/G suffixes:

| Input | Stored as |
|-------|-----------|
| `2.4G` | 2,400,000,000 Hz |
| `100M` | 100,000,000 Hz |
| `10.7k` | 10,700 Hz |
| `1500` | 1,500 Hz |

## Touchstone Parameters

Touchstone files support arbitrary key-value parameters for documenting device settings at the time of measurement. This is useful for devices with multiple operating states like step attenuators, tunable filters, or switches:

```
attenuation: 10 dB
position: through
center_freq: 145 MHz
```

Parameters are set during upload and can be used to filter when retrieving networks via the client library:

```python
nets = client.get_device_networks(device_id, attenuation="10 dB")
```

## Project Layout

```
lab_assets/          Django project settings and root URL config
devices/             Main app — models, views, templates, Touchstone parsing
api/                 REST API — DRF serializers, viewsets, routing
client/              Standalone Python client library (pip-installable)
media/               Uploaded files (in Docker volume)
```
