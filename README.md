# RF Lab Asset Management System

A Django web application for managing home electronics/RF lab devices — attenuators, mixers, cable assemblies, couplers, and more. Upload Touchstone files (.sNp), device photos, and datasheets. View S-parameter plots in the browser. Use the Python client library to pull `skrf.Network` objects directly into measurement scripts for de-embedding.

**[Usage Guide](docs/usage.md)** — asset tags, naming conventions, frequency entry, Touchstone parameters, label printing, and Python client library.

## Deployment

The app runs as a Docker Compose stack — the Django app (gunicorn) and a PostgreSQL database. Designed to run inside a Proxmox LXC container on the lab network.

### Creating the LXC container (Proxmox)

1. **Download a container template.** In the Proxmox web UI, go to your storage (e.g. `local`) → **CT Templates** → **Templates** and download **Debian 12 (Bookworm)** (or Ubuntu 24.04).

2. **Create the container.** Click **Create CT** in the top-right corner and fill in:

   | Setting | Recommended value |
   |---|---|
   | **Hostname** | `lab-assets` |
   | **Password** | Set a root password |
   | **Template** | The Debian/Ubuntu template you just downloaded |
   | **Disk** | 16 GB (plenty for the app, database, and uploaded files) |
   | **CPU** | 2 cores |
   | **Memory** | 2048 MB |
   | **Network** | DHCP or a static IP on your lab VLAN/bridge |

3. **Enable nesting.** Docker requires this. Go to the container → **Options** → **Features** → check **Nesting**. (Alternatively, on the Proxmox host shell: `pct set <CTID> --features nesting=1`.)

4. **Start the container** and open a console (or SSH in).

### Prerequisites

Inside the LXC container, install Docker and Git:

```bash
apt-get update && apt-get install -y docker.io docker-compose-v2 git
systemctl enable --now docker
```

### Installation

```bash
git clone git@github.com:ErikOSorensen/lab_assets.git
cd lab_assets
cp .env.example .env    # then edit .env — see below
docker compose up -d
```

On first start the entrypoint automatically runs migrations, seeds the 19 default device categories, and creates the admin user.

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

The app is reachable at `http://<lxc-ip>:8000` from any machine on the same network. If you have local DNS (e.g. from your router or Pi-hole), point a hostname like `lab-assets.local` at the LXC's IP.

Make sure `DJANGO_ALLOWED_HOSTS` includes every hostname and IP you'll use in the browser, and `DJANGO_CSRF_TRUSTED_ORIGINS` includes the full origin (with `http://` and port) for each.

### Updates

```bash
cd lab_assets
git pull
docker compose up -d --build
```

Migrations are re-run automatically on restart.

### Managing the stack

```bash
docker compose up -d          # Start in background
docker compose logs -f web    # Follow app logs
docker compose restart web    # Restart after config changes
docker compose down           # Stop everything
docker compose down -v        # Stop and delete all data (destructive!)
```

### Backups

Database and uploaded files live in Docker volumes. Back them up regularly.

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

## Local Development (without Docker)

For development you can run directly with SQLite — no Docker or PostgreSQL needed.

```bash
# Requires Python 3.12+ and uv (https://docs.astral.sh/uv/)
git clone git@github.com:ErikOSorensen/lab_assets.git
cd lab_assets
uv sync
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

When no `DATABASE_URL` environment variable is set, SQLite is used automatically.

## Project Layout

```
lab_assets/          Django project settings and root URL config
devices/             Main app — models, views, templates, Touchstone parsing
api/                 REST API — DRF serializers, viewsets, routing
client/              Standalone Python client library (pip-installable)
docs/                Usage guide
media/               Uploaded files (in Docker volume)
```
