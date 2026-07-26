# Zuschnitt – Android Installation Guide

## Overview

The `android/` folder contains a self-contained **Kivy** port of Zuschnitt.
It uses exactly the same core optimizer code as the desktop app, only the UI
is rewritten with Kivy widgets.

---

## Build Prerequisites (on a Linux PC)

| Requirement | Version |
|---|---|
| Python | 3.10 – 3.12 |
| Buildozer | ≥ 1.5 |
| Android NDK | r25c (installed by Buildozer automatically) |
| Android SDK | API 33 (installed by Buildozer automatically) |
| Java JDK | 17 |
| Git | any recent |

### 1 – Install system dependencies

```bash
sudo apt update
sudo apt install -y \
    python3-pip python3-venv \
    git zip unzip openjdk-17-jdk \
    autoconf libtool pkg-config \
    zlib1g-dev libncurses5-dev libncursesw5-dev \
    libtinfo5 cmake libffi-dev libssl-dev
```

### 2 – Install Buildozer

```bash
pip install --user buildozer
```

Verify:

```bash
buildozer --version
```

---

## Build the APK

```bash
cd /path/to/zuschnitt/android
buildozer android debug
```

The first run downloads the Android SDK, NDK and all Python dependencies –
this takes **10–30 minutes** depending on your internet connection.

The finished APK is placed in `android/bin/`:

```
android/bin/zuschnitt-0.1.0-arm64-v8a_armeabi-v7a-debug.apk
```

---

## Install on an Android Device

### Via ADB (USB cable) – recommended during development

1. Enable **Developer Options** on your phone:
   *Settings → About Phone → tap "Build Number" 7 times*

2. Enable **USB Debugging**:
   *Settings → Developer Options → USB Debugging → ON*

3. Connect the phone via USB and run:

```bash
adb install android/bin/zuschnitt-*.apk
```

4. The app appears in the app drawer as **Zuschnitt**.

### Via file transfer (no USB Debugging needed)

1. Enable **Install from Unknown Sources**:
   - Android 8+: *Settings → Apps → Special App Access →
     Install Unknown Apps → your file manager → Allow*

2. Copy the `.apk` file to your phone (USB, Bluetooth, cloud storage, email …).

3. Open the file on the phone and tap **Install**.

---

## Runtime Usage on Android

| Feature | Notes |
|---|---|
| **2D Sheet Cutting** | Enter stock sheets and pieces, tap Optimize |
| **1D Bar Cutting** | Switch to 1D mode from the main screen |
| **Settings** | Kerf (saw blade width), units, rotation |
| **Open / Save** | Projects saved as `.zusc` files in your chosen folder |
| **Export PDF** | Saved to `/sdcard/Download/<project>.pdf` |

---

## Release Build (for distribution outside Play Store)

1. Create a keystore (one-time):

```bash
keytool -genkey -v -keystore my-release-key.jks \
  -keyalg RSA -keysize 2048 -validity 10000 \
  -alias zuschnitt
```

2. Edit `buildozer.spec`:

```ini
android.debug = False
android.release_artifact = aab         # or apk
android.keystore = /path/to/my-release-key.jks
android.keyalias = zuschnitt
android.keystore_password = yourpassword
android.keyalias_password = yourpassword
```

3. Build:

```bash
buildozer android release
```

---

## Troubleshooting

| Problem | Solution |
|---|---|
| `adb: command not found` | `sudo apt install adb` or install Android Studio platform tools |
| Build fails on NDK | Delete `.buildozer/` and rebuild; first run re-downloads NDK |
| "App not installed" | Uninstall any older debug version first |
| Black screen on launch | Check logcat: `adb logcat | grep python` |
| Storage permission denied | Grant *Files* permission manually in Settings → App Info |

---

## Updating the App

After changing Python source files:

```bash
cd android
buildozer android debug deploy run
```

This rebuilds only changed Python modules (much faster than the first build).
