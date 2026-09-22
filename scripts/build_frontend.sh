#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$PROJECT_ROOT/frontend"
TARGET_DIR="$PROJECT_ROOT/app/static"

mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/pages" "$TARGET_DIR/images" "$TARGET_DIR/resources"
cp -R "$SOURCE_DIR/pages"/. "$TARGET_DIR/pages"/
cp -R "$SOURCE_DIR/images"/. "$TARGET_DIR/images"/
cp -R "$SOURCE_DIR/resources"/. "$TARGET_DIR/resources"/

echo "Frontend prepared in app/static."
