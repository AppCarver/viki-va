#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "🚀 Starting V.I.K.I. services (production-like mode)..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Bring up services using the main docker-compose file
docker-compose -f ./deployment/docker-compose.yml up --build

echo "✅ V.I.K.I. services started successfully."
echo "Access your VA through its designated entry points."