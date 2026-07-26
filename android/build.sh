#!/usr/bin/env bash
# build.sh – Build Zuschnitt APK using the official kivy/buildozer Docker image.
# Usage:  bash build.sh [buildozer-args...]   default: android debug
#
# Requirements:  Docker (running)
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ARGS="${*:-android debug}"

echo "==> Building Zuschnitt APK with kivy/buildozer Docker image"
echo "    Source: $SCRIPT_DIR"
echo "    Args:   $ARGS"
echo ""

# The kivy/buildozer image entrypoint IS buildozer — pass args directly.
# warn_on_root=0 in buildozer.spec suppresses the root warning inside Docker.
docker run --rm \
    -v "$SCRIPT_DIR":/home/user/hostcwd \
    kivy/buildozer $ARGS

echo ""
echo "==> Done. APK is in $SCRIPT_DIR/bin/"
