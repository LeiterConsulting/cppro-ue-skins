# Night Shift artwork

All Night Shift artwork is original clean-room project material released under
the repository's MIT license. It was procedurally drawn for this example with
Pillow. No artwork, code, names, or other assets from After Dark or another
commercial screensaver package are included.

The creative lineage is the broad 1990s screensaver idea of a tiny autonomous
world continuing its work while the viewer watches. The city, service craft,
palette, silhouettes, and interaction marks are new.

## Runtime assets

| Asset | Dimensions | Purpose |
| --- | ---: | --- |
| `Substrate_Base.png` | 1920×550 | Opaque midnight skyline and roofscape |
| `Substrate_Flow_00.png` | 2000×590 | Transparent sky traffic and blinking lanes |
| `Substrate_Flow_01.png` | 2000×590 | Slower trains and window lights |
| `Damage_Tear.png` | 256×256 | Local illuminated service-call beacon |
| `Mender_Frame_00..15.png` | 160×112 | Service-craft patrol, alarm, travel, and repair states |

The two motion layers include 40 pixels of bleed on each axis so their small
translations never reveal the screen edge.

## Regenerate

Install the repository requirements, then run:

```powershell
python -m pip install -r requirements.txt
python examples/night-shift/tools/generate-cleanroom-trio-assets.py
```

The example-local generator defaults to Night Shift and writes the exact
authoring contract to `generated/art`. Its theme seed is fixed at `0xA17E`.

After changing artwork:

1. Reimport the PNGs into `/Game/CPPRO/MenderSwarmA1/Textures`.
2. Keep them in the UI texture group, non-streaming, and sRGB.
3. Preserve true RGBA transparency on flow, beacon, and craft images.
4. Cook Android ASTC content and verify the canonical entry map.
5. Test under the transparent keybed; small desktop details lose contrast on
   the physical panel.
