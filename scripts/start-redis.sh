#!/bin/bash
# Script to start Redis in Docker with auto-restart

echo "Starting Redis container..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Check if container already exists
if docker ps -a | grep -q redis-acad-ai; then
    echo "Redis container exists. Starting it..."
    docker start redis-acad-ai
else
    echo "Creating and starting Redis container..."
    docker run -d \
        --name redis-acad-ai \
        --restart unless-stopped \
        -p 6379:6379 \
        redis
fi

# Wait a moment for Redis to start
sleep 2

# Verify Redis is running
if docker exec redis-acad-ai redis-cli ping > /dev/null 2>&1; then
    echo "✓ Redis is running on localhost:6379"
    echo "✓ Container will auto-start on system boot (--restart unless-stopped)"
else
    echo "✗ Redis failed to start. Check logs with: docker logs redis-acad-ai"
    exit 1
fi

