# CPPRO UE Skins

An independent, experimental authoring kit for original interactive Unreal
Engine skins on the Finalmouse Centerpiece Pro.

This repository packages the useful result of the work—not the lab notebook.
It contains a minimal UE4.27 project, a clean-room SkinApi authoring stub, the
physically calibrated key layout, designer tools, and complete device-tested
examples. It does **not** contain captures, firmware, vendor software, extracted
official skins, exploratory probes, or private development artifacts.

> This is not an official Finalmouse SDK. Custom PAK loading is experimental
> and can reset a skin slot if a build crashes. Keep another known-good slot
> available and use a nonessential slot while developing.

![Keyfield A2 layout preview](examples/keyfield-a2/generated/keyfield-a2.svg)

![Koi Pond background](examples/koi-pond/source-art/pond-background-chatgpt.jpg)

## Skins available

| Skin | Type | What it demonstrates | Download and documentation |
| --- | --- | --- | --- |
| Keyfield A2 | Interactive app shell | All 68 mapped keys, press/release effects, palettes, readable display regions, and Ready/Live/Paused states | [Keyfield A2](examples/keyfield-a2/README.md) |
| Koi Pond | Living physics sandbox | Full-screen artwork, animated koi, continuous swimming, water ripples, and key-position physics impulses | [Koi Pond](examples/koi-pond/README.md) |

Each example includes its exact release PAK and SHA-256 checksum. Koi Pond also
includes its original artwork, generated animation frames, frame-preparation
tool, editable UE4.27 assets, and canonical source-map snapshot.

## What works

- UE4.27 Android ASTC content packaged as PAK version 11.
- Canonical entry map `/Game/map/M_EntryPoint`.
- 1920×550 device viewport.
- All 68 physically mapped key regions.
- SkinApi `OnKeyEvent(HCode, IsActuated, Percentage)` binding.
- Reliable per-key press and release edges.
- Bounded UMG animation, pooled key effects, and application states.
- Hybrid UMG/physics scenes with animated actors and key-position impulses.
- Readable content in the keyboard's key-free display regions.
- Direct, explicit PAK upload to slots 1–5.

The installed device runtime currently reports `Percentage=100` for a press;
continuous analog depth is not available to the skin callback. Design device
skins around `IsActuated` unless later firmware proves otherwise.

## Repository map

| Path | Purpose |
| --- | --- |
| `project/` | Minimal editable UE4.27 `spark` project and SkinApi stub |
| `examples/keyfield-a2/` | App-state and calibrated keyfield example |
| `examples/koi-pond/` | Living physics scene, original art, source map, and PAK |
| `layout/` | Calibrated display geometry and native index map |
| `schemas/` | JSON contracts for skins, profiles, and themes |
| `tools/cppro_skin_kit.py` | Validate, preview, and lock designer inputs |
| `tools/build-pak.ps1` | Cook Android ASTC and create a slot-compatible PAK |
| `tools/verify-pak.ps1` | Check integrity, mount layout, map, and SHA-256 |
| `tools/cppro_upload.py` | Dry-run-by-default slot installer |
| `reference/runtime/` | Dependency-free input/state/profile reference model |
| `docs/` | Setup, authoring, packaging, input, and safety guides |

## Quick start

Requirements:

- Windows 10/11
- Unreal Engine **4.27**
- UE4.27 Android toolchain configured for Android ASTC cooking
- PowerShell 5.1 or newer
- Python 3.10+; `pywinusb` is needed only for uploading

Clone and validate the included design:

```powershell
git clone https://github.com/LeiterConsulting/cppro-ue-skins.git
cd cppro-ue-skins

python tools/cppro_skin_kit.py validate `
  examples/keyfield-a2/manifest/skin.json

python tools/cppro_skin_kit.py preview `
  examples/keyfield-a2/manifest/skin.json `
  --out artifacts/keyfield-a2.svg

python -m unittest discover -s reference/runtime -v
```

Open `project/spark.uproject` in UE4.27. The included startup map launches
Keyfield A2. Duplicate the A2 actor/widget into a new content folder, edit the
copy, place it in `/Game/map/M_EntryPoint`, and keep that canonical map path.

Build:

```powershell
./tools/build-pak.ps1 `
  -EngineRoot 'D:\Epic Games\UE_4.27' `
  -OutPak '.\artifacts\my_skin.pak'
```

Verify:

```powershell
./tools/verify-pak.ps1 `
  -Pak '.\artifacts\my_skin.pak' `
  -EngineRoot 'D:\Epic Games\UE_4.27'
```

Upload only after reviewing the safety guide:

```powershell
python -m venv .venv
./.venv/Scripts/pip.exe install -r requirements.txt

# Dry run: prepares and describes the transfer without touching the keyboard.
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 5 --pak .\artifacts\my_skin.pak

# Explicit device write.
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 5 --pak .\artifacts\my_skin.pak --send --activate
```

Start with [Getting Started](docs/getting-started.md), then read the
[Authoring Guide](docs/authoring-guide.md) and
[Safety and Compatibility](docs/safety-and-compatibility.md).

## Keyfield A2

The included example PAK was physically accepted and remained stable while
typing. It starts in Ready, Enter begins/resumes, Escape pauses, Backspace
resets, and Tab cycles palettes. Its exact SHA-256 is:

```text
639F4258E74B0230C37D7F62F8AB541D6B8E829CAC6CA1D19A7E5E36D4BDFDA4
```

See [examples/keyfield-a2/README.md](examples/keyfield-a2/README.md).

## Koi Pond

Koi Pond is a full-keyboard ambient physics sandbox. Six animated koi roam over
an underwater scene; every physical key produces a three-stage water ripple and
an impulse at that key's calibrated position. The example demonstrates shared
sprite animation, persistent steering, world-to-UMG synchronization, bounded
physics, and crop-safe full-viewport artwork.

Its exact release PAK, editable UE4.27 assets, canonical map snapshot,
ChatGPT-created source artwork, generated animation frames, and reproduction
tool are included. See
[examples/koi-pond/README.md](examples/koi-pond/README.md).

## License and support

This is an early community authoring surface built from confirmed behavior, not
a vendor-supported compatibility promise. It is provided free of charge and
without warranty or support.

Original project code, documentation, manifests, tooling, and example artwork
are open source under the [MIT License](LICENSE). You may use, modify,
redistribute, sublicense, or sell copies subject to the license's short notice
requirement. Third-party technology and trademarks remain subject to their own
terms; see [NOTICE.md](NOTICE.md).
