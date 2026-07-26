# Moodfield

Moodfield is an adaptive, always-live keyboard skin. Its full-screen substrate
breathes at rest, deforms under individual keys, and builds persistent color
geography from the way the keyboard is being used.

It does not need the words being typed. Numeric key positions, timing,
repetition, cadence, and rolling spatial memories are enough to distinguish
broad bilateral typing from compact control patterns such as WASD, UHJK, IJKL,
or the arrow cluster.

## What it demonstrates

- A full-screen generated material that remains alive without input.
- Exact localized contact for all 68 mapped keys.
- Three-contact paths and rebound waves without particle allocation.
- Persistent top/middle/bottom × left/right alpha-row heat memory.
- A weighted basin that moves and resizes with repeated patterns.
- General compact-cluster recognition plus a fast dedicated WASD path.
- Active, retained, and cool-afterglow visual phases.
- A session-local Caps Lock indicator beneath the physical Caps key.
- A fixed-cost Blueprint-to-material state bridge suitable for daily use.

## Behavior

| Input pattern | Visual response |
| --- | --- |
| Press one key | A localized depression, rim, and shallow rebound appear under that key |
| Type normal prose | Broad bilateral alpha use builds a cohesive, slowly migrating mood basin |
| Repeat a word or favor a row | The basin shifts and resizes toward the repeated geography |
| Use a compact key cluster | The corresponding region becomes focused and more immediate |
| Use WASD repeatedly | A fast game-mode focus forms over the left control region |
| Use arrows/navigation | Exact contacts remain visible; navigation weighting is intentionally subtle |
| Stop typing | The basin holds, cools toward violet/blue, then fades |
| Resume after a pause | The retained map wakes progressively over the first short sequence |
| Press Caps Lock | The warm Caps tint alternates once per physical press |

The number row produces exact contact and activity, but it is not currently
part of the six-zone prose geography. Arrow input is tracked as a secondary
navigation signal, but the release hardware test did not produce a distinct
arrow-mode mood comparable to the immediately visible WASD focus.

## Contents

| Path | Purpose |
| --- | --- |
| `ARCHITECTURE.md` | Classifier, material, lifecycle, privacy, performance, and tuning design |
| `manifest/` | Reviewable layout, palette, and semantic-control contracts |
| `generated/moodfield.svg` | Desktop preview of the calibrated key surface |
| `generated/moodfield.lock.json` | Resolved manifest and source hashes |
| `project-overlay/CPPRO/` | Exact path-sensitive actor, widget, material, and MPC assets used by the release |
| `project-map/M_EntryPoint.umap` | Exact canonical source map for this skin |
| `release/cppro_moodfield.pak` | Exact slot-compatible release artifact |
| `../../tools/ue-moodfield-build.py` | Generated material source |
| `../../project/Source/spark/MoodfieldAuthoringLibrary.*` | Blueprint bridge generator and self-test |

The JSON manifest drives validation and the static layout preview. Moodfield's
adaptive runtime is authored by the included Python/C++ generator because the
basic manifest schema intentionally does not attempt to compile arbitrary
Blueprint classifiers or material code.

## Load the included PAK

Review [Safety and Compatibility](../../docs/safety-and-compatibility.md), then
verify the artifact:

```powershell
./tools/verify-pak.ps1 `
  -Pak .\examples\moodfield\release\cppro_moodfield.pak `
  -EngineRoot 'D:\Epic Games\UE_4.27' `
  -ExpectedAssets `
    'spark/Content/CPPRO/KeyfieldPulse/BP_KeyfieldPulse.uasset', `
    'spark/Content/CPPRO/KeyfieldPulse/WBP_KeyfieldPulse.uasset', `
    'spark/Content/CPPRO/Moodfield/Materials/M_MoodfieldSurface.uasset', `
    'spark/Content/CPPRO/Moodfield/Materials/MPC_Moodfield.uasset'
```

Prepare a dry run for any slot:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 2 `
  --pak .\examples\moodfield\release\cppro_moodfield.pak
```

Write only when ready:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 2 `
  --pak .\examples\moodfield\release\cppro_moodfield.pak `
  --send --activate
```

The release is 32,198,369 bytes. Its SHA-256 is:

```text
EE43EE4EE0BCE6B3F2BFB67A8B3F174AE00ED2B59E896235AF6B454D92D2C6F5
```

The PAK was uploaded and activated on physical hardware in slot 2. Normal
typing, generalized localized patterns, the dedicated WASD response, key
contact, multi-key input, lifecycle color, number-row limitation, subtle arrow
weighting, and stable runtime behavior were verified. The same identity is
recorded in `release/SHA256SUMS.txt` and the generated loader catalog.

## Open and edit the exact release source

The release keeps the proven `/Game/CPPRO/KeyfieldPulse` package paths. Apply
the example overlay and map to a clean checkout:

```powershell
Copy-Item `
  .\examples\moodfield\project-overlay\CPPRO\* `
  .\project\Content\CPPRO\ `
  -Recurse -Force

Copy-Item `
  .\examples\moodfield\project-map\M_EntryPoint.umap `
  .\project\Content\map\M_EntryPoint.umap `
  -Force
```

Open `project/spark.uproject` in UE4.27. The exact runtime assets appear under
`/Game/CPPRO/KeyfieldPulse` and `/Game/CPPRO/Moodfield/Materials`.

To regenerate the material and apply the classifier bridge to a working copy of
Keyfield Pulse, compile the editor project and run:

```powershell
& 'D:\Epic Games\UE_4.27\Engine\Binaries\Win64\UE4Editor-Cmd.exe' `
  .\project\spark.uproject `
  -run=pythonscript `
  "-script=exec(open(r'tools/ue-moodfield-build.py', encoding='utf-8').read())" `
  -unattended -nop4 -nullrhi -NoSound
```

Restore the clean repository project after experimenting:

```powershell
git restore project/Content/CPPRO/KeyfieldPulse
git restore project/Content/map/M_EntryPoint.umap
```

Keep the canonical map path `/Game/map/M_EntryPoint`, preserve the native
`0..67` mapping, and run the tests listed in the architecture tuning guide
before loading a rebuilt PAK.
