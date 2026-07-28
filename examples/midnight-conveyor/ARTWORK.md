# Midnight Conveyor artwork

All artwork is original clean-room material released under this repository's
MIT license. It was procedurally created with Pillow for this example. No
assets from After Dark or another commercial screensaver product are included.

The design uses the general tradition of autonomous factory scenes: belts keep
moving, packages circulate, and small workers respond to new jobs.

## Runtime assets

| Asset | Dimensions | Purpose |
| --- | ---: | --- |
| `Substrate_Base.png` | 1920×550 | Opaque factory, four belts, machinery, and floor |
| `Substrate_Flow_00.png` | 2000×590 | Transparent moving belt arrows |
| `Substrate_Flow_01.png` | 2000×590 | Transparent moving parcels |
| `Damage_Tear.png` | 256×256 | Local parcel/sorting marker |
| `Mender_Frame_00..15.png` | 160×112 | Sorter-bot patrol, alarm, travel, and work states |

## Regenerate

```powershell
python -m pip install -r requirements.txt
python examples/midnight-conveyor/tools/generate-cleanroom-trio-assets.py
```

The local generator defaults to Midnight Conveyor, writes to `generated/art`,
and uses fixed seed `0xC0DE`.

After editing:

1. Reimport the PNGs into `/Game/CPPRO/MenderSwarmA1/Textures`.
2. Use the UI texture group, disable streaming, and preserve sRGB.
3. Keep transparent assets as true RGBA.
4. Cook Android ASTC content and verify the canonical entry map.
5. Validate motion and contrast on the physical panel.
