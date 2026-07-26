#!/usr/bin/env bash
# build.sh – Build Zuschnitt APK using the official kivy/buildozer Docker image.
# Usage:  bash build.sh [buildozer-args...]   default: android debug
#
# Requirements:  Docker (running), kivy/buildozer image pulled
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARGS="${*:-android debug}"

# Mount the host ~/.buildozer cache into the container so that the already-
# downloaded Android SDK/NDK/ANT are reused across runs.
HOST_CACHE="$HOME/.buildozer"
mkdir -p "$HOST_CACHE"

echo "==> Building Zuschnitt APK with kivy/buildozer Docker image"
echo "    Source : $SCRIPT_DIR"
echo "    Cache  : $HOST_CACHE → /home/user/.buildozer (inside container)"
echo "    Args   : $ARGS"
echo ""

# The image entrypoint IS buildozer — pass args directly (no 'bash -c').
# warn_on_root=0 in buildozer.spec silences the root-user prompt.
docker run --rm \
    -v "$SCRIPT_DIR":/home/user/hostcwd \
    -v "$HOST_CACHE":/home/user/.buildozer \
    kivy/buildozer $ARGS

echo ""
echo "==> Done. APK is in $SCRIPT_DIR/bin/"
