#!/bin/bash

set -e

if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found."
    echo "Run the setup script first."
    exit 1
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Preparing frontend..."
./scripts/build_frontend.sh

echo "Starting application..."
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
