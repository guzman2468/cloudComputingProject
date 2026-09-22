#!/bin/bash
set -e

echo "Building and starting the application container..."
docker compose up --build
