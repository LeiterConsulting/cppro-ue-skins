# Mender Swarm artwork

All Mender Swarm artwork is original project material released under the
repository's MIT license.

The five-state prototype atlas was drawn procedurally for this example. The
substrate, flow layers, damage mark, and sixteen runtime frames are generated
locally by `tools/generate-mender-assets.py`.

## Source atlas

| Property | Value |
| --- | --- |
| File | `source-art/T_MenderPrototypeAtlas.svg` |
| Raster derivative | `source-art/T_MenderPrototypeAtlas.png` |
| Dimensions | 1280×256 RGBA |
| Cells | Five 256×256 frames |
| Background | Transparent |
| States | Patrol, startled, travel, repair, recover |

| Cell | X range | State |
| ---: | ---: | --- |
| 0 | 0–255 | Patrol |
| 1 | 256–511 | Startled |
| 2 | 512–767 | Travel |
| 3 | 768–1023 | Repair |
| 4 | 1024–1279 | Recover |

The source palette is cyan and white so state-specific warm, cool, and
magenta treatments can be added without losing internal contrast. The frames
represent posture; orientation comes from runtime heading.

## Generated assets

| Asset | Dimensions | Purpose |
| --- | ---: | --- |
| `Substrate_Base.png` | 1920×550 | Opaque full-panel fabric, passive devices, and woven structure |
| `Substrate_Flow_00.png` | 2000×590 | Sparse transparent environmental motion |
| `Substrate_Flow_01.png` | 2000×590 | Second phase-shifted motion layer |
| `Damage_Tear.png` | 256×256 | Local membrane deformation and radial tear |
| `Mender_Frame_00..15.png` | 160×112 | State-colored runtime presentation sequence |

The oversized flow layers provide enough bleed for small position transforms
without revealing an edge. The substrate contains passive micro-devices, while
the twelve larger animated menders are the visible active crew.

## Regenerate

Install the repository requirements, then run:

```powershell
python -m pip install -r requirements.txt
python examples/mender-swarm/tools/generate-mender-assets.py
```

The generator uses a fixed seed (`0xC0FFEE`) and writes to
`examples/mender-swarm/generated/art`. Re-running it with the committed source
atlas reproduces the derived PNG set.

After changing artwork:

1. Reimport the changed PNGs into
   `/Game/CPPRO/MenderSwarmA1/Textures`.
2. Keep UI textures in the UI texture group, non-streaming, and sRGB.
3. Preserve transparent pixels as true RGBA transparency.
4. Cook Android ASTC content and verify the canonical map.
5. Test under the physical keybed; fine desktop details are softened by the
   panel, ASTC compression, and transparent switches.

The source-art hashes are recorded in `source-art/SHA256SUMS.txt`.
