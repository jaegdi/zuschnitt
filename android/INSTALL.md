# Zuschnitt – Android Installation Guide

## Overview

The `android/` folder contains a self-contained **Kivy** port of Zuschnitt.
It uses exactly the same core optimizer code as the desktop app; only the UI
is rewritten with Kivy widgets.

---

## Build Prerequisites

| Requirement | Notes |
|---|---|
| **Docker** | Recommended — avoids all host-dependency issues |
| OR Linux host | Python 3.10–3.12, Java JDK 17, git, zip |
| Android device | Android 8.0+ (API 26+) |
| ADB (optional) | For USB install; not needed for file-transfer install |

---

## Build the APK (recommended: Docker)

Using the official `kivy/buildozer` Docker image is the most reliable method
because it provides a clean, controlled build environment regardless of your
host system's Python or library versions.

### 1 – Install Docker

**openSUSE / Tumbleweed:**
```bash
sudo zypper install docker
sudo systemctl enable --now docker
sudo usermod -aG docker $USER   # log out & back in after this
```

**Ubuntu / Debian:**
```bash
sudo apt install docker.io
sudo systemctl enable --now docker
sudo usermod -aG docker $USER
```

Verify Docker works (no `sudo`):
```bash
docker run --rm hello-world
```

### 2 – Pull the Kivy buildozer image (one-time, ≈ 2 GB)

```bash
docker pull kivy/buildozer
```

### 3 – Build the APK

```bash
cd /path/to/zuschnitt/android
bash build.sh
```

`build.sh` mounts the `android/` folder into the container and runs
`buildozer android debug`. The **first build** takes **15–30 minutes**
(downloads NDK r28c, Android SDK, compiles Kivy). Subsequent builds are
much faster because `.buildozer/` is cached on your host.

The finished APK appears in `android/bin/`:

```
android/bin/zuschnitt-0.1.0-arm64-v8a_armeabi-v7a-debug.apk
```

### 4 – What `build.sh` does internally

```bash
docker run --rm \
    -v "$ANDROID_DIR":/home/user/hostcwd \
    kivy/buildozer \
    android debug
```

The `android/` folder is mounted at `/home/user/hostcwd` (the container's
working directory). The image's entrypoint IS `buildozer`, so arguments are
passed directly. Build artefacts (`.buildozer/`, `bin/`) are written back
to your host folder.

> **Note:** `buildozer.spec` sets `warn_on_root = 0` because Docker runs
> as root by default — without this buildozer prompts interactively and hangs.

---

## Alternative: Native Linux Build

> **Note:** Building natively on Python 3.13+ can fail with
> `ModuleNotFoundError: No module named '_posixsubprocess'` due to
> incompatibilities between the host Python and the hostpython3 recipe.
> Use the Docker method above if you encounter this error.

### System dependencies (openSUSE / Tumbleweed)

```bash
sudo zypper install -y \
    python313 python313-pip python313-venv \
    java-17-openjdk git zip unzip \
    autoconf libtool pkg-config cmake \
    zlib-devel libffi-devel openssl-devel
```

### System dependencies (Ubuntu / Debian)

```bash
sudo apt install -y \
    python3-pip python3-venv \
    openjdk-17-jdk git zip unzip \
    autoconf libtool pkg-config cmake \
    zlib1g-dev libffi-dev libssl-dev
```

### Install Buildozer (requires Python 3.10–3.12)

```bash
cd /path/to/zuschnitt
python3 -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/kivy/buildozer.git"
pip install "python-for-android" "cython>=3.0"
```

### Build

```bash
cd android
source ../.venv/bin/activate    # must activate so cython is in PATH
buildozer android debug
```

---

## Install on an Android Device

### Via ADB (USB cable) – recommended during development

1. Enable **Developer Options** on your phone:
   *Settings → About Phone → tap "Build Number" 7 times*

2. Enable **USB Debugging**:
   *Settings → Developer Options → USB Debugging → ON*

3. Connect via USB and run:

```bash
adb install android/bin/zuschnitt-*.apk
```

### Via file transfer (no USB Debugging needed)

1. Enable **Install from Unknown Sources**:
   *Settings → Apps → Special App Access → Install Unknown Apps →
   your file manager → Allow*

2. Copy the `.apk` to your phone (USB cable, Bluetooth, cloud storage, email…).

3. Open the file on the phone → tap **Install**.

---

## Runtime Usage on Android

| Feature | Notes |
|---|---|
| **2D Sheet Cutting** | Enter stock sheets and pieces, tap Optimize |
| **1D Bar Cutting** | Switch to 1D mode from the main screen |
| **Settings** | Kerf (saw blade width), units, rotation |
| **Open / Save** | Projects saved as `.zusc` files |
| **Export PDF** | Saved to `/sdcard/Download/<project>.pdf` |

---

## Release Build (for distribution)

1. Create a keystore (one-time):

```bash
keytool -genkey -v -keystore my-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias zuschnitt
```

2. Edit `buildozer.spec`:

```ini
android.debug = False
android.keystore = /path/to/my-release-key.jks
android.keyalias = zuschnitt
android.keystore_password = yourpassword
android.keyalias_password = yourpassword
```

3. Build with Docker:

```bash
bash build.sh android release
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `_posixsubprocess` error | Use `bash build.sh` (Docker method) |
| `cython not found` | Must activate venv: `source .venv/bin/activate` |
| `adb: command not found` | `sudo zypper install android-tools` or install Android Studio platform tools |
| Build fails on NDK | Delete `.buildozer/` and rebuild; Docker will re-download |
| "App not installed" | Uninstall any older debug version first |
| Black screen on launch | `adb logcat \| grep python` to see errors |
| Storage permission denied | Grant *Files* permission in Settings → App Info |

---

## Updating the App

After changing Python source files:

```bash
cd android
bash build.sh android debug
# then install:
adb install -r bin/zuschnitt-*.apk
```
