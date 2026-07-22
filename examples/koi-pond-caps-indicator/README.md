# Koi Pond: Caps Indicator

This is an additional, stateful variant of [Koi Pond](../koi-pond/README.md).
The pond, six animated koi, continuous steering, per-key ripples, and physics
impulses remain intact. A translucent orange layer beneath the physical Caps
Lock key now shows a device-session-local on/off state.

The variant answers a practical question: how can a skin retain a Boolean state
when the callback supplies momentary key activity and an analog key may repeat
`IsActuated=true` reports while held?

## What it demonstrates

- Correct physical placement under native layout index/HCode `32` (Caps Lock).
- A persistent integer state initialized to `0`.
- A separate edge latch that allows exactly one toggle per physical press.
- Passive and active opacity states without replacing the pond artwork.
- Reuse of the complete Koi Pond scene instead of duplicating its artwork and
  shared runtime assets.
- A tested pattern suitable for mode, profile, layer, or feature indicators.

## Behavior

The Caps layer is always present at low opacity so its placement is visible.
Each new Caps Lock press alternates it between:

| State | Stored value | Layer opacity |
| --- | ---: | ---: |
| Passive/off | `0` | `0.22` |
| Active/on | `1` | `0.90` |

The input graph behaves as follows:

```text
Caps ACT=true and edge latch=false
  -> set edge latch=true
  -> toggle state 0 <-> 1
  -> apply opacity for the new state

Caps ACT=true and edge latch=true
  -> ignore repeated held report

Caps ACT=false
  -> set edge latch=false
  -> retain state
```

The state variable and edge latch must remain separate. Using `IsActuated`
itself as the displayed state only produces a momentary press/release flash;
toggling on every actuated report can change state several times during one
physical hold.

## Important limitation

This is a **session-local visual indicator**, not authoritative host Caps Lock
telemetry. The confirmed `SkinApi` callback exposes `HCode`, `IsActuated`, and
`Percentage`; it does not expose:

- the host operating system's Caps Lock or keyboard LED state;
- the character ultimately produced by the host (`a` versus `A`);
- keyboard-layout, IME, or application text state.

The indicator therefore begins at off whenever the skin loads and tracks Caps
press edges received while it remains active. If the host began in the opposite
state, manually resynchronize the visual indicator. A future host bridge or
plugin API that exposes lock state could make synchronization authoritative.

## Contents

| Path | Purpose |
| --- | --- |
| `project-map/M_EntryPoint.umap` | Exact canonical source map for this variant |
| `release/cppro_koi_pond_caps_indicator.pak` | Exact hardware-tested upload artifact |
| `../../project/Content/CPPRO/KoiCapsL1/` | Editable UE4.27 state actor and widget |
| `../koi-pond/source-art/` | Shared ChatGPT-created pond and koi artwork |
| `../../project/Content/CPPRO/TouchPoolL1/` | Shared Koi Pond scene assets |

The state actor and widget retain their internal `KoiCapsL1` package names
because cooked Unreal references are path-sensitive.

## Load the included PAK

Review [Safety and Compatibility](../../docs/safety-and-compatibility.md), then
verify the artifact:

```powershell
./tools/verify-pak.ps1 `
  -Pak .\examples\koi-pond-caps-indicator\release\cppro_koi_pond_caps_indicator.pak `
  -EngineRoot 'D:\Epic Games\UE_4.27' `
  -ExpectedAssets `
    'spark/Content/CPPRO/KoiCapsL1/BP_KoiCapsL1.uasset', `
    'spark/Content/CPPRO/KoiCapsL1/WBP_KoiCapsL1.uasset'
```

Prepare a dry run for any slot:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 4 `
  --pak .\examples\koi-pond-caps-indicator\release\cppro_koi_pond_caps_indicator.pak
```

Write only when ready:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 4 `
  --pak .\examples\koi-pond-caps-indicator\release\cppro_koi_pond_caps_indicator.pak `
  --send --activate
```

The release is 33,590,359 bytes. Its SHA-256 is:

```text
BA28F85334051C9B3B8742C407F22BCE7EFD996B0DB57DE05B679EE0CA0602A9
```

The upload and activation path was verified on physical hardware in slot 4.
The indicator was confirmed at the physical Caps Lock key and alternated across
successive presses while the koi pond remained stable.

## Open and edit the source

Replace the repository's default entry map with this example snapshot:

```powershell
Copy-Item `
  .\examples\koi-pond-caps-indicator\project-map\M_EntryPoint.umap `
  .\project\Content\map\M_EntryPoint.umap `
  -Force
```

Open `project/spark.uproject` in UE4.27. The additional assets appear under
`/Game/CPPRO/KoiCapsL1`; their scene dependencies remain under
`/Game/CPPRO/TouchPoolL1`.

Restore the default map with:

```powershell
git restore project/Content/map/M_EntryPoint.umap
```

Build with the same Android ASTC workflow documented for the base Koi Pond
example. Keep the canonical map path `/Game/map/M_EntryPoint`, preserve the
native `0..67` input-index mapping, and test state changes on both press and
release edges before loading a rebuilt PAK.
