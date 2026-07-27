# Mender Swarm

Mender Swarm turns the full CPPRO panel into a synthetic fabric maintained by
twelve visible micro-machines. The substrate remains alive at rest. Pressing a
key disturbs the nearby machines and leaves a persistent tear at the physical
key location. A three-mender crew then travels to that wound while the mark
slowly repairs.

Four wounds can remain active simultaneously, so ordinary typing produces
several visible jobs instead of making the entire swarm chase only the last
key pressed.

![Mender Swarm substrate](generated/art/Substrate_Base.png)

## What it demonstrates

- A full-screen 1920×550 illustrated substrate with lightweight continuous
  motion.
- Twelve persistent UMG agents driven by invisible physics proxies.
- Exact impact placement for all 68 confirmed native key indices.
- Four concurrent, independently fading damage sites.
- Four three-mender work crews with varied commitment strengths.
- Continuous exploration when no repair job is active.
- Local collision impulses, soft boundaries, and non-settling motion.
- Sixteen presentation frames derived from five original authored states.
- A session-local Caps Lock indicator beneath the physical Caps key.
- A stable fixed-size runtime with no per-press actor or widget allocation.

## Behavior

| Input | Response |
| --- | --- |
| Press a key | A localized impact appears and nearby menders react |
| Release the key | The damage remains and begins its roughly 6.5-second repair fade |
| Press keys in separated regions | Up to four wounds coexist and different three-mender crews travel toward them |
| Continue typing | Each channel accepts newer work without erasing the other three jobs |
| Stop typing | Crews finish their current jobs, then return to independent exploration |
| Press Caps Lock | The thematic Caps indicator alternates once per physical press |

The four work channels are deterministic: native key index `0..67` selects
channel `index mod 4`. A new press replaces only that channel's previous work
site. This bounded design is predictable on the keyboard runtime and prevents
an unbounded queue from growing during fast typing.

## Contents

| Path | Purpose |
| --- | --- |
| `ARCHITECTURE.md` | Runtime layers, input routing, repair crews, steering, and performance design |
| `ARTWORK.md` | Original art provenance, dimensions, states, and regeneration instructions |
| `source-art/` | Original five-state vector atlas and its raster derivative |
| `generated/art/` | Exact substrate, flow, damage, and 16 mender PNGs used to author the release |
| `tools/generate-mender-assets.py` | Deterministic Pillow-based artwork generator |
| `project-overlay/CPPRO/MenderSwarmA1/` | Editable actor, widget, and texture assets used by the release |
| `project-map/M_EntryPoint.umap` | Exact canonical source map for this skin |
| `release/cppro_mender_swarm.pak` | Device-tested, slot-compatible release artifact |
| `library.json` | Metadata compiled into the desktop loader catalog |

## Load the included PAK

Review [Safety and Compatibility](../../docs/safety-and-compatibility.md), then
verify the artifact:

```powershell
./tools/verify-pak.ps1 `
  -Pak .\examples\mender-swarm\release\cppro_mender_swarm.pak `
  -EngineRoot 'D:\Epic Games\UE_4.27' `
  -ExpectedAssets `
    'spark/Content/CPPRO/MenderSwarmA1/BP_MenderSwarmA1.uasset', `
    'spark/Content/CPPRO/MenderSwarmA1/WBP_MenderSwarmA1.uasset', `
    'spark/Content/CPPRO/MenderSwarmA1/Textures/Substrate_Base.uasset', `
    'spark/Content/CPPRO/MenderSwarmA1/Textures/Damage_Tear.uasset'
```

Prepare a dry run for any slot:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 2 `
  --pak .\examples\mender-swarm\release\cppro_mender_swarm.pak
```

Write only when ready:

```powershell
./.venv/Scripts/python.exe tools/cppro_upload.py `
  --slot 2 `
  --pak .\examples\mender-swarm\release\cppro_mender_swarm.pak `
  --send --activate
```

The release is 33,700,843 bytes. Its SHA-256 is:

```text
2E4AFA331A09745D3AC1F1EB795952192ABDDC517C4671478C94BC392E3893E3
```

The PAK was uploaded and activated on physical hardware in slot 2. Full-screen
rendering, stable frame rate, mapped impacts, persistent damage, multiple work
sites, moving menders, multi-key input, and Caps state were verified. The same
identity appears in `release/SHA256SUMS.txt` and the generated loader catalog.

## Open and edit the exact release source

Apply the example overlay and map to a clean checkout:

```powershell
Copy-Item `
  .\examples\mender-swarm\project-overlay\CPPRO\MenderSwarmA1 `
  .\project\Content\CPPRO\ `
  -Recurse -Force

Copy-Item `
  .\examples\mender-swarm\project-map\M_EntryPoint.umap `
  .\project\Content\map\M_EntryPoint.umap `
  -Force
```

Open `project/spark.uproject` in UE4.27. The runtime actor, widget, and imported
textures appear under `/Game/CPPRO/MenderSwarmA1`.

The actor Blueprint owns the key-event routing and physics controller. The
widget owns the substrate, moving flow layers, damage images, presentation
sprites, and Caps tint. Preserve these object paths and the canonical
`/Game/map/M_EntryPoint` map when cooking a compatible replacement PAK.

To regenerate the original artwork before reimporting it:

```powershell
python .\examples\mender-swarm\tools\generate-mender-assets.py
```

The installed runtime reports `Percentage=100` for a press, so this skin uses
press/release edges and time rather than continuous analog depth.
