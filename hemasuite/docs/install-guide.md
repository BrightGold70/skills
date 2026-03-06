# HemaSuite - Install Guide

## From .dmg file

1. Double-click the `.dmg` file to open it
2. Drag **HemaSuite** to the **Applications** folder
3. Open **Applications** in Finder
4. **Right-click** HemaSuite > click **Open**
5. A dialog will appear: "macOS cannot verify the developer..." > click **Open**
6. HemaSuite will launch. Future launches: just double-click as normal.

## From USB drive

1. Connect the USB drive
2. Drag **HemaSuite.app** to your **Applications** folder
3. Double-click to open (no security dialog needed)

## Troubleshooting

### "HemaSuite can't be opened because it is from an unidentified developer"

Open **Terminal** (search in Spotlight) and run:

```
xattr -cr /Applications/HemaSuite.app
```

Then double-click HemaSuite again.

### App seems frozen on startup

HemaSuite loads R and Python engines on first launch. This may take 10-30 seconds. Wait for the spinner to finish.

### App won't open at all

1. Delete HemaSuite from Applications
2. Re-copy from the .dmg or USB
3. Try the right-click > Open method again

## Updating

1. Quit HemaSuite if running
2. Delete the old HemaSuite.app from Applications
3. Install the new version following the steps above

## System Requirements

- macOS 13 (Ventura) or later
- About 1 GB free disk space
- No additional software needed (R and Python are bundled)

## Contact

For help, contact Hawk Kim, M.D., Ph.D.
