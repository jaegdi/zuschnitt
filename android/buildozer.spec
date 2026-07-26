[app]

# App title and identity
title = Zuschnitt
package.name = zuschnitt
package.domain = org.zuschnitt

source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,zusc

# App version
version = 0.1.0

# Python requirements — must be installable via pip
requirements = python3,kivy==2.3.0,reportlab,Pillow

# Orientation: allow both portrait and landscape on tablets
orientation = all

# Application icon (optional — place icon.png in android/)
#icon.filename = icon.png

# Buildozer / p4a internals
android.permissions = WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE,INTERNET

# Target Android API (Android 13)
android.api = 33
android.minapi = 26
android.ndk = 25c

# Architecture: build for arm64 (modern phones) + armeabi-v7a (older)
android.archs = arm64-v8a, armeabi-v7a

# Debug keystore (change to release.keystore for Google Play)
android.debug = True

# Logcat filter
android.logcat_filters = *:S python:D

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = ./.buildozer
bin_dir = ./bin
