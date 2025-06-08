#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

echo "👨‍💻 Starting V.I.K.I. services in development mode..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
  echo "Error: Docker is not running. Please start Docker and try again."
  exit 1
fi

# Bring up services using both the main and dev docker-compose files
# The dev file will typically add volumes for live reloading, expose more ports, etc.
docker-compose -f ./deployment/docker-compose.yml -f ./deployment/docker-compose.dev.yml up --build

echo "✅ V.I.K.I. dev services started successfully."
echo "Your development environment is now running. Changes to code in 'src/' will often auto-reload."