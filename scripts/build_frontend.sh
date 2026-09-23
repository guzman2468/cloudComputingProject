#!/bin/bash
set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SOURCE_DIR="$PROJECT_ROOT/frontend"
TARGET_DIR="$PROJECT_ROOT/app/static"

mkdir -p "$TARGET_DIR"
mkdir -p "$TARGET_DIR/pages" "$TARGET_DIR/images" "$TARGET_DIR/resources"
mkdir -p "$PROJECT_ROOT/app/templates"

# HTML is served through explicit FastAPI routes. Copy only styles/scripts to
# the public StaticFiles directory so page documents are never published there.
for asset in "$SOURCE_DIR/pages"/*.css "$SOURCE_DIR/pages"/*.js; do
    [ -f "$asset" ] && cp "$asset" "$TARGET_DIR/pages/"
done
cp -R "$SOURCE_DIR/images"/. "$TARGET_DIR/images"/
cp -R "$SOURCE_DIR/resources"/. "$TARGET_DIR/resources"/
cp "$SOURCE_DIR/pages"/*.html "$PROJECT_ROOT/app/templates/"

echo "Frontend prepared in app/static."
