# Design: HemaSuite Personal Distribution

## Plan Reference

`docs/01-plan/features/hemasuite-personal-distribution.plan.md`

## Design Overview

Simplify HemaSuite's distribution pipeline for personal delivery to < 10 macOS hematologists. Remove public distribution infrastructure, add developer credit to splash screens, and create a one-command build-to-DMG script.

## Component Design

### C1: Splash Screen — Developer Credit

Add "Developed by Hawk Kim, M.D., Ph.D." to both splash screens.

#### `src/splash.html` (Tauri native splash — shown during sidecar boot)

Add a new `.credit` paragraph below the `.status` line:

```html
<p class="status">Starting up...</p>
<p class="credit">Developed by Hawk Kim, M.D., Ph.D.</p>
```

CSS for `.credit`:
```css
.credit {
  color: #475569;
  font-size: 0.75rem;
  margin-top: 2rem;
  letter-spacing: 0.02em;
}
```

#### `src/components/SplashScreen.tsx` (React splash — shown in-app)

Add a credit line below the "Starting up..." text:

```tsx
<p className="text-slate-500 text-sm">Starting up...</p>
<p className="text-slate-600 text-xs mt-8 tracking-wide">
  Developed by Hawk Kim, M.D., Ph.D.
</p>
```

### C2: Build Script — `scripts/build-dmg.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION=$(grep '"version"' src-tauri/tauri.conf.json | head -1 | sed 's/.*: *"\(.*\)".*/\1/')
APP_NAME="HemaSuite"
APP_PATH="src-tauri/target/release/bundle/macos/${APP_NAME}.app"
DMG_PATH="dist/${APP_NAME}-${VERSION}.dmg"

echo "Building ${APP_NAME} v${VERSION}..."

# Step 1: Build release
cargo tauri build --release

# Step 2: Ad-hoc sign
codesign -s - --deep --force "${APP_PATH}"
echo "Ad-hoc signed: ${APP_PATH}"

# Step 3: Create DMG
mkdir -p dist
create-dmg \
  --volname "${APP_NAME} ${VERSION}" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 100 \
  --icon "${APP_NAME}.app" 150 190 \
  --app-drop-link 450 190 \
  "${DMG_PATH}" \
  "${APP_PATH}"

echo "DMG created: ${DMG_PATH}"
echo "Size: $(du -h "${DMG_PATH}" | cut -f1)"
```

**Dependencies**: `brew install create-dmg`

### C3: Remove Notarization/Updater

#### Files to delete:
- `scripts/sign-and-notarize.sh` (if exists)

#### Config changes in `src-tauri/tauri.conf.json`:
- Remove the `updater` section entirely
- Remove any `APPLE_SIGNING_IDENTITY`, `APPLE_ID`, `APPLE_TEAM_ID` references

#### Entitlements (`src-tauri/entitlements.plist`):
Keep only:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "...">
<plist version="1.0">
<dict>
  <key>com.apple.security.network.client</key>
  <true/>
  <key>com.apple.security.files.user-selected.read-write</key>
  <true/>
</dict>
</plist>
```

Remove: `com.apple.security.app-sandbox` (not needed without App Store)

### C4: First-Launch Dialog

React component shown once on first app open (persisted via `localStorage`):

```tsx
// src/components/FirstLaunchDialog.tsx
export function FirstLaunchDialog({ onDismiss }: { onDismiss: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-800 rounded-lg p-6 max-w-md text-white space-y-4">
        <h2 className="text-xl font-semibold">Welcome to HemaSuite</h2>
        <p className="text-slate-300 text-sm">
          If macOS showed a security warning when opening this app,
          right-click the app icon and select <strong>Open</strong>,
          then click <strong>Open</strong> in the dialog.
        </p>
        <p className="text-slate-400 text-xs">
          This only needs to be done once. Future launches will work normally.
        </p>
        <button
          onClick={onDismiss}
          className="w-full bg-blue-600 hover:bg-blue-700 rounded px-4 py-2 text-sm font-medium"
        >
          Got it
        </button>
      </div>
    </div>
  );
}
```

Trigger logic in `App.tsx`:
```tsx
const [showFirstLaunch, setShowFirstLaunch] = useState(
  () => !localStorage.getItem('hemasuite-first-launch-dismissed')
);

const handleDismiss = () => {
  localStorage.setItem('hemasuite-first-launch-dismissed', 'true');
  setShowFirstLaunch(false);
};
```

### C5: Install Guide — `docs/install-guide.md`

Target audience: non-developer hematologists.

Sections:
1. **From .dmg** — open, drag to Applications, right-click > Open
2. **From USB** — drag to Applications, double-click (no security dialog)
3. **Troubleshooting** — Terminal `xattr -cr` command
4. **Updating** — delete old version, install new
5. **System requirements** — macOS 12+ (Monterey), 1GB free disk space

### C6: Distribution Doc — `DISTRIBUTION.md`

Internal-only document for the developer:
1. **Prerequisites** — Rust, Node.js, create-dmg, Xcode CLI tools
2. **Build** — `./scripts/build-dmg.sh`
3. **Versioning** — How to bump version in `Cargo.toml` + `tauri.conf.json`
4. **Distribution checklist** — test on clean Mac, share via AirDrop/USB, confirm launch
5. **Changelog** — version history

## Implementation Order

| Order | Task | Component | Files Modified/Created |
|-------|------|-----------|----------------------|
| 1 | Developer credit on splash | C1 | `src/splash.html`, `src/components/SplashScreen.tsx`, `SplashScreen.test.tsx` |
| 2 | Remove notarization/updater | C3 | `tauri.conf.json`, `entitlements.plist`, delete `sign-and-notarize.sh` |
| 3 | Build DMG script | C2 | `scripts/build-dmg.sh` (new) |
| 4 | First-launch dialog | C4 | `src/components/FirstLaunchDialog.tsx` (new), `App.tsx` |
| 5 | Install guide | C5 | `docs/install-guide.md` (new) |
| 6 | Distribution doc | C6 | `DISTRIBUTION.md` (new) |

## Testing Strategy

| Test | Method |
|------|--------|
| Splash screen credit renders | Update `SplashScreen.test.tsx` — assert "Hawk Kim" text present |
| Build script succeeds | Manual: run `scripts/build-dmg.sh`, verify .dmg output |
| .dmg installs correctly | Manual: mount .dmg, drag to Applications, launch |
| Gatekeeper bypass works | Manual: right-click > Open on a clean user account |
| First-launch dialog shows once | Unit test: renders on first load, hidden after dismiss |
| Install guide accuracy | Manual: follow guide on a colleague's Mac |

## Data Flow

```
Developer Machine                    Recipient Mac
─────────────────                    ──────────────
cargo tauri build
  → .app bundle
  → codesign -s - (ad-hoc)
  → create-dmg
  → HemaSuite-{ver}.dmg
  → AirDrop / USB ──────────────→  Open .dmg
                                    Drag to /Applications
                                    Right-click > Open (once)
                                    ✓ App launches
                                    ✓ Splash: "Developed by Hawk Kim, M.D., Ph.D."
                                    ✓ First-launch dialog (once)
                                    ✓ Ready to use
```
