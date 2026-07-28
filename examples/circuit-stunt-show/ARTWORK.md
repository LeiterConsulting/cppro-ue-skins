# Circuit Stunt Show artwork

All artwork is original clean-room project material released under the MIT
license. It was procedurally authored for this example with Pillow. No artwork,
code, names, or other assets from After Dark or any commercial screensaver
package are included.

Its inspiration is the general screensaver tradition of tiny characters
performing elaborate autonomous routines. The circuit arena, riders, ramps,
palette, current effects, and landing marker are new.

## Runtime assets

| Asset | Dimensions | Purpose |
| --- | ---: | --- |
| `Substrate_Base.png` | 1920×550 | Opaque circuit-board arena, ramps, loops, and traces |
| `Substrate_Flow_00.png` | 2000×590 | Transparent current traveling through major traces |
| `Substrate_Flow_01.png` | 2000×590 | Transparent sparks and accent motion |
| `Damage_Tear.png` | 256×256 | Local stunt/landing marker |
| `Mender_Frame_00..15.png` | 160×112 | Rider cruise, airborne, alarm, and landing states |

## Regenerate

```powershell
python -m pip install -r requirements.txt
python examples/circuit-stunt-show/tools/generate-cleanroom-trio-assets.py
```

The example-local generator defaults to Circuit Stunt Show, writes to
`generated/art`, and uses fixed seed `0xB17E`.

After changing artwork:

1. Reimport PNGs into `/Game/CPPRO/MenderSwarmA1/Textures`.
2. Use the UI texture group, disable streaming, and retain sRGB.
3. Preserve true transparency on current, spark, marker, and rider files.
4. Cook Android ASTC content and verify `/Game/map/M_EntryPoint`.
5. Test on the physical panel, where the keybed changes apparent contrast.
