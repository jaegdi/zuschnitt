# Zuschnitt – Native Android App (Kotlin + Chaquopy)

## Overview

Native Android app using **Kotlin + Jetpack Compose** for the UI and **Chaquopy** to embed the Python optimizer core.

**Why this approach:**
- ✅ Fast native UI — no startup delays, smooth Material Design 3
- ✅ Reuses the tested Python optimizer (no rewrite needed)
- ✅ Works offline (Python interpreter embedded in the APK)

---

## Build with Android Studio

### 1. Install Android Studio

Download from https://developer.android.com/studio

### 2. Open the project

```bash
Android Studio → Open → select /path/to/zuschnitt/android-kotlin/
```

Wait for Gradle sync to complete (first sync downloads dependencies).

### 3. Run on device or emulator

- Connect an Android device via USB with USB Debugging enabled
- OR create an emulator: *Tools → Device Manager → Create Virtual Device*
- Click **▶ Run** in Android Studio

The APK will be installed and launched automatically.

### 4. Build a release APK

```bash
./gradlew assembleRelease
```

Output: `app/build/outputs/apk/release/app-release-unsigned.apk`

Sign it:
```bash
keytool -genkey -v -keystore release.jks -keyalg RSA -keysize 2048 -validity 10000 -alias zuschnitt
jarsigner -verbose -sigalg SHA256withRSA -digestalg SHA-256 \
  -keystore release.jks \
  app/build/outputs/apk/release/app-release-unsigned.apk zuschnitt
```

---

## Install on Device

### Via Android Studio

Click **▶ Run** — Android Studio installs automatically.

### Via ADB

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

### Via file transfer

Copy the APK to your phone, open it, and tap **Install**.

---

## Architecture

```
UI Layer (Kotlin/Compose)
    ↓
Chaquopy Bridge
    ↓
Python Optimizer Core (embedded in APK)
```

**UI**: `MainActivity.kt` — Jetpack Compose with Material 3  
**Bridge**: `OptimizerBridge.kt` — calls Python via Chaquopy  
**Core**: `app/src/main/python/zuschnitt/` — copied from `src/zuschnitt/core/`

---

## Development Notes

- **Chaquopy** bundles Python 3.11 + stdlib automatically
- **Pure Python dependencies** work out-of-the-box (`pip { install "..." }` in `build.gradle`)
- **No native compilation** — the optimizer is pure Python, no C extensions
- **Python stdlib** is included (json, dataclasses, etc.)

---

## Troubleshooting

| Problem | Solution |
|---|---|
| Gradle sync fails | Ensure Android SDK 34 is installed: *Tools → SDK Manager* |
| App crashes on startup | Check logcat: `adb logcat \| grep zuschnitt` |
| Python import error | Verify Python files are in `app/src/main/python/zuschnitt/` |
| Slow first launch | Python interpreter extracts on first run (~3 sec delay) |

---

## Tech Stack

- **Language**: Kotlin 2.0+
- **UI**: Jetpack Compose + Material 3
- **Build**: Gradle 8.7+
- **Python**: Chaquopy 15.0.1 (Python 3.11 embedded)
- **Min SDK**: API 24 (Android 7.0)
- **Target SDK**: API 34 (Android 14)
