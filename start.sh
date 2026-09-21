#!/bin/bash

set -e

if [ ! -d ".venv" ]; then
    echo "ERROR: Virtual environment not found."
    echo "Run the setup script first."
    exit 1
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Starting application..."
python -m uvicorn app.main:app --reload
