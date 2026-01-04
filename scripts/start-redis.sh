#!/bin/bash
# Script to start Redis in Docker with auto-restart

echo "Starting Redis container..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Get Redis port from environment or use default
REDIS_PORT=${REDIS_PORT:-6379}
CONTAINER_NAME=${REDIS_CONTAINER_NAME:-redis-acad-ai}

# Check if container is already running
if docker ps | grep -q "$CONTAINER_NAME"; then
    echo "Redis container '$CONTAINER_NAME' is already running on port $REDIS_PORT"
    exit 0
fi

# Check if container exists but is stopped
if docker ps -a | grep -q "$CONTAINER_NAME"; then
    echo "Redis container '$CONTAINER_NAME' exists but is stopped. Starting it..."
    docker start "$CONTAINER_NAME"
else
    echo "Creating and starting Redis container '$CONTAINER_NAME' on port $REDIS_PORT..."
    docker run -d \
        --name "$CONTAINER_NAME" \
        --restart unless-stopped \
        -p "${REDIS_PORT}:6379" \
        redis:7-alpine
fi

# Wait a moment for Redis to start
sleep 2

# Verify Redis is running
if docker exec "$CONTAINER_NAME" redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is running on localhost:$REDIS_PORT"
    echo "✓ Container will auto-start on system boot (--restart unless-stopped)"
else
    echo "✗ Redis failed to start. Check logs with: docker logs $CONTAINER_NAME"
    exit 1
fi

