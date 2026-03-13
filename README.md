# RF Lab Asset Management System

A Django web application for managing home electronics/RF lab devices — attenuators, mixers, cable assemblies, couplers, and more. Upload Touchstone files (.sNp), device photos, and datasheets. View S-parameter plots in the browser. Use the Python client library to pull `skrf.Network` objects directly into measurement scripts for de-embedding.

## Docker Deployment (recommended)

The simplest way to run the app is with Docker Compose. This gives you the Django app with gunicorn and a PostgreSQL database.

```bash
git clone <repo-url>
cd lab_assets

# Start everything
docker compose up -d

# That's it — the app is at http://localhost:8000
# Default login: admin / admin
```

On first start, the entrypoint automatically runs migrations, seeds categories, and creates the admin user.

### Configuration

Create a `.env` file to override defaults:

```env
# Generate a real key: python -c "import secrets; print(secrets.token_urlsafe(50))"
DJANGO_SECRET_KEY=your-secret-key-here

# Change the default admin password
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_PASSWORD=your-password-here
DJANGO_SUPERUSER_EMAIL=you@example.com

# If accessing from other machines on the lab network
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,lab-server.local,192.168.1.50
DJANGO_CSRF_TRUSTED_ORIGINS=http://lab-server.local:8000,http://192.168.1.50:8000

# Database password
POSTGRES_PASSWORD=lab_assets_dev

# Change the exposed port
WEB_PORT=8000
```

### Managing the container

```bash
docker compose up -d          # Start in background
docker compose logs -f web    # Follow app logs
docker compose down           # Stop
docker compose down -v        # Stop and delete database volume (destructive!)
```

### Backups

Database and uploaded files are stored in Docker volumes. To back up:

```bash
# Database dump
docker compose exec db pg_dump -U lab_assets lab_assets > backup.sql

# Restore
docker compose exec -T db psql -U lab_assets lab_assets < backup.sql

# Media files are in the media_data volume
docker compose cp web:/app/media ./media-backup
```

## Local Development (without Docker)

For development, you can run directly with SQLite:

### Requirements

- Python 3.12+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) package manager

### Setup

```bash
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

Device categories are created automatically during migration.

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
