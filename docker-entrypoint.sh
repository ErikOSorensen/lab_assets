#!/bin/bash
set -e

# Wait for the database to be ready
echo "Waiting for database..."
while ! uv run python -c "
import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lab_assets.settings')
django.setup()
from django.db import connection
connection.ensure_connection()
" 2>/dev/null; do
    sleep 1
done
echo "Database ready."

# Run migrations
echo "Applying migrations..."
uv run python manage.py migrate --noinput

# Create superuser if it doesn't exist and credentials are provided
if [ -n "$DJANGO_SUPERUSER_USERNAME" ]; then
    uv run python manage.py shell -c "
from django.contrib.auth.models import User
if not User.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists():
    User.objects.create_superuser(
        '$DJANGO_SUPERUSER_USERNAME',
        '${DJANGO_SUPERUSER_EMAIL:-admin@localhost}',
        '$DJANGO_SUPERUSER_PASSWORD',
    )
    print('Superuser created: $DJANGO_SUPERUSER_USERNAME')
else:
    print('Superuser already exists.')
"
fi

exec "$@"
