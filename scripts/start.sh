#!/bin/bash
set -e

echo "Starting Acad AI Assessment Engine (Production Mode)..."

# Check Redis connection
echo "Checking Redis connection..."
REDIS_URL=${REDIS_URL:-redis://localhost:6379/0}
python3 << EOF
import sys
import os
try:
    import redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print(f"Redis is running at {redis_url}")
    except (redis.ConnectionError, redis.TimeoutError) as e:
        print(f"ERROR: Redis at {redis_url} is not running. Please start Redis before continuing.")
        sys.exit(1)
except ImportError:
    print("WARNING: redis package not found. Skipping Redis check. Make sure Redis is running at", redis_url)
EOF
if [ $? -ne 0 ]; then
    exit 1
fi

echo "Waiting for database to be ready..."
while ! python manage.py check --database default 2>/dev/null; do
    echo "Waiting for database..."
    sleep 2
done

echo "Running migrations..."
python manage.py migrate --noinput

echo "Creating admin user..."
python manage.py shell << EOF
import os
import django
django.setup()

from apps.accounts.models import User

admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
admin_password = os.getenv('ADMIN_PASSWORD', 'admin12345')
admin_username = os.getenv('ADMIN_USERNAME', 'admin')

if not User.objects.filter(email=admin_email).exists():
    User.objects.create_superuser(
        username=admin_username,
        email=admin_email,
        password=admin_password,
        is_student=False
    )
    print(f'Admin user created: {admin_email}')
else:
    print(f'Admin user already exists: {admin_email}')
EOF

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

echo "Checking for existing Celery processes..."
if [ -f /tmp/celery-worker.pid ]; then
    OLD_PID=$(cat /tmp/celery-worker.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping existing Celery worker (PID: $OLD_PID)..."
        kill $OLD_PID 2>/dev/null || true
        sleep 1
    fi
    rm -f /tmp/celery-worker.pid
fi

if [ -f /tmp/celery-beat.pid ]; then
    OLD_PID=$(cat /tmp/celery-beat.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "Stopping existing Celery beat (PID: $OLD_PID)..."
        kill $OLD_PID 2>/dev/null || true
        sleep 1
    fi
    rm -f /tmp/celery-beat.pid
fi

echo "Starting Celery worker in background..."
celery -A config worker -l info --detach --logfile=/tmp/celery-worker.log --pidfile=/tmp/celery-worker.pid

echo "Starting Celery beat in background..."
celery -A config beat -l info --detach --logfile=/tmp/celery-beat.log --pidfile=/tmp/celery-beat.pid

echo "Starting Django application with Daphne (ASGI) for WebSocket support..."
echo "Production mode: No auto-reload (for auto-reload, use scripts/start-dev.sh)"
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application

