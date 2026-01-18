#!/bin/bash

# dev_init.sh
# Automates the startup of the Dionysus 3.0 Development Environment
# 1. Establishes SSH Tunnel to VPS
# 2. Starts Docker Services
# 3. Verifies API Health

VPS_USER="mani"
VPS_HOST="72.61.78.89"
KEY_PATH="$HOME/.ssh/mani_vps"

echo "🚀 Initializing Dionysus 3.0 Dev Environment..."

# 1. Check/Start SSH Tunnel
if pgrep -f "ssh -f -N -L 7687:localhost:7687" > /dev/null; then
    echo "✅ SSH Tunnel (Neo4j) already active."
else
    echo "🔌 Establishing SSH Tunnel to $VPS_HOST..."
    ssh -f -N -L 7474:localhost:7474 -L 7687:localhost:7687 -i "$KEY_PATH" "$VPS_USER@$VPS_HOST"
    if [ $? -eq 0 ]; then
        echo "✅ SSH Tunnel established."
    else
        echo "❌ Failed to establish SSH Tunnel."
        exit 1
    fi
fi

# 2. Docker Compose Up
echo "🐳 Starting Docker Services..."
docker-compose up -d
if [ $? -ne 0 ]; then
    echo "❌ Docker Compose failed."
    exit 1
fi

# 3. Wait for API Health
echo "⏳ Waiting for API to be healthy..."
max_retries=30
count=0
while [ $count -lt $max_retries ]; do
    if curl -s http://localhost:8000/health > /dev/null; then
        echo "✅ API is Healthy and Ready."
        exit 0
    fi
    printf "."
    sleep 2
    count=$((count + 1))
done

echo "\n❌ API failed to become healthy after 60 seconds."
echo "Check logs with: docker logs dionysus-api"
exit 1
