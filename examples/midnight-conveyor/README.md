# Midnight Conveyor

Midnight Conveyor turns the CPPRO into a compact automated sorting floor. Four
production lanes keep moving at idle while twelve sorter bots patrol the
machinery. Every mapped key press introduces a persistent parcel at that
physical location, recruiting one three-bot crew without pulling the other
crews away from their existing jobs.

![Midnight Conveyor factory](generated/art/Substrate_Base.png)

## What it demonstrates

- Four full-width production lines rendered across the 1920×550 panel.
- Layered belt arrows and parcels that move continuously at low fixed cost.
- Twelve animated sorter bots controlled by bounded physics proxies.
- Exact localized input for all 68 confirmed native key indices.
- Four concurrent parcel jobs and independent three-bot crews.
- A session-local Caps Lock indicator beneath the physical Caps key.
- A fixed-size runtime with no object allocation during typing.

## Behavior

| Input | Response |
| --- | --- |
| Press a key | A parcel marker appears at that physical key |
| Release the key | The parcel persists while its assigned crew processes it |
| Press separated keys | Four sorting jobs can remain active simultaneously |
| Stop typing | Bots complete their work and return to independent patrol |
| Press Caps Lock | The thematic Caps layer alternates once per physical press |

## Contents

| Path | Purpose |
| --- | --- |
| `ARCHITECTURE.md` | Runtime layers, work channels, input routing, and performance design |
| `ARTWORK.md` | Original art provenance, exact asset contract, and regeneration |
| `generated/art/` | Factory, belt, parcel, and sorter-bot PNGs used by the release |
| `tools/generate-cleanroom-trio-assets.py` | Deterministic Pillow artwork generator |
| `project-overlay/CPPRO/MenderSwarmA1/` | Editable actor, widget, and imported texture assets |
| `project-map/M_EntryPoint.umap` | Canonical source map |
| `release/cppro_midnight_conveyor_a1.pak` | Device-tested release artifact |
| `library.json` | Desktop-loader metadata |

## Load the included PAK

Review [Safety and Compatibility](../../docs/safety-and-compatibility.md), then:

```powershell
./tools/verify-pak.ps1 `
  -Pak .\examples\midnight-conveyor\release\cppro_midnight_conveyor_a1.pak `
  -EngineRoot 'D:\Epic Games\UE_4.27' `
  -ExpectedAssets `
    'spark/Content/CPPRO/MenderSwarmA1/BP_MenderSwarmA1.uasset', `
    'spark/Content/CPPRO/MenderSwarmA1/WBP_MenderSwarmA1.uasset', `
    'spark/Content/CPPRO/MenderSwarmA1/Textures/Substrate_Base.uasset', `
    'spark/Content/CPPRO/MenderSwarmA1/Textures/Damage_Tear.uasset'
```

Dry run:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 2 `
  --pak .\examples\midnight-conveyor\release\cppro_midnight_conveyor_a1.pak
```

Write and activate:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 2 `
  --pak .\examples\midnight-conveyor\release\cppro_midnight_conveyor_a1.pak `
  --send --activate
```

The release is 32,631,572 bytes. Its SHA-256 is:

```text
D7C9C144C04869639E4442340E2A255E1B4BF935FDE21A682E25A770C393D79A
```

The PAK passed UnrealPak integrity checks and was uploaded and activated on
physical hardware in slot 2.

## Open and edit the exact source

```powershell
Copy-Item `
  .\examples\midnight-conveyor\project-overlay\CPPRO\MenderSwarmA1 `
  .\project\Content\CPPRO\ `
  -Recurse -Force

Copy-Item `
  .\examples\midnight-conveyor\project-map\M_EntryPoint.umap `
  .\project\Content\map\M_EntryPoint.umap `
  -Force
```

Open `project/spark.uproject` in UE4.27. Preserve
`/Game/CPPRO/MenderSwarmA1` and `/Game/map/M_EntryPoint` when cooking.

Regenerate the exact artwork:

```powershell
python .\examples\midnight-conveyor\tools\generate-cleanroom-trio-assets.py
```

The installed runtime reports `Percentage=100`, so the skin responds to
press/release edges and time rather than continuous analog travel.
