# Keyfield Pulse

Keyfield Pulse turns the calibrated Keyfield interaction system into a clean,
always-live keyboard skin. It retains the colorful press lights, hold-sensitive
release pads, and three-stage waves from the earlier experiments while removing
the calibration boxes, key labels, app-state controls, and safe-region debug UI.

The result is a practical daily-use skin rather than a test bench: the display
stays nearly black until typing animates the physical keyfield.

## What it demonstrates

- Correct visual placement for all 68 physical keys.
- Immediate per-key light on actuation.
- A bounded release pad whose size reflects hold duration.
- Three sequential wave stages on release.
- Row-colored effects on a clean, full-screen background.
- A session-local Caps Lock indicator beneath the physical Caps Lock key.
- An always-live interaction model without Ready, Paused, or diagnostic modes.

## Behavior

| Input | Visual response |
| --- | --- |
| Press any key | Its mapped key region illuminates immediately |
| Hold a key | The eventual release pad grows, capped at 750 ms |
| Release a key | The key fades and emits a bounded pad plus three-stage wave |
| Press Caps Lock | The orange Caps layer alternates between passive and active |

Multiple held keys respond independently. The release effects use fixed pools
for the 68-key layout and do not create unbounded widgets while typing.

## Caps indicator

Caps Lock uses native layout index/HCode `32`. Its visual state is stored in an
integer initialized to `0`, while a separate press-edge latch ignores repeated
`IsActuated=true` reports from the analog keyboard during one physical hold.
Successive press edges alternate the layer between:

| State | Stored value | Layer opacity |
| --- | ---: | ---: |
| Passive/off | `0` | `0.22` |
| Active/on | `1` | `0.90` |

This state is local to the loaded skin. The confirmed runtime callback does not
expose the host operating system's Caps Lock state or composed characters, so
the indicator begins off whenever the skin loads. See
[Koi Pond: Caps Indicator](../koi-pond-caps-indicator/README.md) for the reusable
edge-latched state pattern and its limitations.

## Contents

| Path | Purpose |
| --- | --- |
| `manifest/` | Reviewable design, theme, and control contracts |
| `generated/keyfield-pulse.svg` | Desktop preview of the calibrated layout |
| `generated/keyfield-pulse.lock.json` | Resolved configuration and source hashes |
| `project-map/M_EntryPoint.umap` | Exact canonical source map for this skin |
| `release/cppro_keyfield_pulse.pak` | Exact hardware-tested upload artifact |
| `../../project/Content/CPPRO/KeyfieldPulse/` | Editable UE4.27 actor and widget |

The JSON manifest is a validated design contract and preview source, not a
general JSON-to-Blueprint compiler. Runtime behavior lives in the included
Blueprint assets.

## Load the included PAK

Review [Safety and Compatibility](../../docs/safety-and-compatibility.md), then
verify the artifact:

```powershell
./tools/verify-pak.ps1 `
  -Pak .\examples\keyfield-pulse\release\cppro_keyfield_pulse.pak `
  -EngineRoot 'D:\Epic Games\UE_4.27' `
  -ExpectedAssets `
    'spark/Content/CPPRO/KeyfieldPulse/BP_KeyfieldPulse.uasset', `
    'spark/Content/CPPRO/KeyfieldPulse/WBP_KeyfieldPulse.uasset'
```

Prepare a dry run for any slot:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 2 `
  --pak .\examples\keyfield-pulse\release\cppro_keyfield_pulse.pak
```

Write only when ready:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 2 `
  --pak .\examples\keyfield-pulse\release\cppro_keyfield_pulse.pak `
  --send --activate
```

The release is 32,164,255 bytes. Its SHA-256 is:

```text
2E2FB2C4D58FE1E87DE4287BE9A953B2C7E34DEA73965CE4C9C1822EA4B716B8
```

The PAK was accepted and activated on physical hardware in slot 2. All mapped
key interactions, multi-key input, and Caps state toggling were confirmed. The
final cleanup build also removed every calibration and safe-zone panel.

## Open and edit the source

Activate this example's canonical map in the repository project:

```powershell
Copy-Item `
  .\examples\keyfield-pulse\project-map\M_EntryPoint.umap `
  .\project\Content\map\M_EntryPoint.umap `
  -Force
```

Open `project/spark.uproject` in UE4.27. The actor and widget appear under
`/Game/CPPRO/KeyfieldPulse`.

Restore the repository's default Keyfield A2 map with:

```powershell
git restore project/Content/map/M_EntryPoint.umap
```

Keep the canonical map path `/Game/map/M_EntryPoint`, preserve the native
`0..67` input-index mapping, and validate both press and release behavior before
uploading a rebuilt PAK.
