# Zuschnitt Android App – Quick Start

## Option 1: Build in Android Studio (Recommended)

1. **Install Android Studio**  
   Download from https://developer.android.com/studio

2. **Open project**  
   Android Studio → Open → select `android-kotlin/`

3. **Wait for Gradle sync** (first time downloads ~500 MB)

4. **Run**  
   - Connect Android device with USB Debugging enabled  
   - OR create emulator: *Tools → Device Manager → Create Virtual Device*  
   - Click **▶ Run**

## Option 2: Command Line Build

```bash
cd android-kotlin
./gradlew assembleDebug
```

Output: `app/build/outputs/apk/debug/app-debug.apk`

Install:
```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Current Status

✅ **Working:**
- Native Kotlin UI with Material 3
- Python optimizer embedded via Chaquopy
- Basic input screens for sheets and pieces
- Optimizer call from Kotlin to Python

⚠️ **TODO:**
- Full input forms (add/edit/delete sheets/pieces)
- Visual sheet layout rendering (Canvas)
- PDF export
- File save/load (.zusc format)
- Settings screen (kerf, rotation, units)

## Development Roadmap

### Phase 1: Input UI ✅
- [x] Basic Compose layout
- [ ] Sheet input form
- [ ] Piece input form
- [ ] List management (add/delete/edit)

### Phase 2: Optimizer Integration ✅
- [x] Chaquopy setup
- [x] Python bridge module
- [x] Call optimizer from Kotlin

### Phase 3: Visualization
- [ ] Canvas-based sheet renderer
- [ ] Zoom/pan gestures
- [ ] Color-coded pieces
- [ ] Cut lines with numbers

### Phase 4: Export
- [ ] PDF generation (Android PdfDocument API)
- [ ] Share intent for PDFs

### Phase 5: File Management
- [ ] .zusc JSON save/load
- [ ] File picker integration
- [ ] Recent files list

## Tech Stack

- **UI**: Jetpack Compose + Material 3
- **Language**: Kotlin 2.1
- **Build**: Gradle 8.11
- **Python**: 3.11 embedded via Chaquopy 15.0
- **Min SDK**: API 24 (Android 7.0)
- **Target SDK**: API 35 (Android 15)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Gradle sync fails | Install Android SDK 35: *Tools → SDK Manager → Android 15.0* |
| App crashes on startup | Check logcat: `adb logcat \| grep -i python` |
| Python import error | Verify `app/src/main/python/zuschnitt/*.py` files exist |
| Slow first launch | Python runtime extracts on first run (~3 sec) |
| Build timeout | Increase Gradle memory: `org.gradle.jvmargs=-Xmx4g` in `gradle.properties` |

## Next Steps for Development

1. **Implement full input forms** — `InputScreen.kt` with add/edit/delete
2. **Add Canvas visualization** — `SheetCanvas.kt` custom composable
3. **Port PDF export** — use Android's `PdfDocument` class
4. **Add file picker** — use `ActivityResultContracts.OpenDocument`
5. **Settings persistence** — use `DataStore` for preferences
