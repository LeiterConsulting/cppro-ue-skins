# Input and layout

## Callback

The minimal Blueprint-facing event is:

```text
OnKeyEvent(HCode: byte, IsActuated: bool, Percentage: int32)
```

On the tested device runtime:

- `HCode` is a native physical index from 0 through 67.
- `IsActuated=true` is press; `false` is release.
- `Percentage` remains 100 on press and is not a usable analog depth stream.

The `SkinApi` plugin in `project/Plugins` is a cook-time clean-room declaration.
The device supplies the real runtime module.

## Geometry

`layout/cppro-key-layout-v1.json` contains:

- calibrated 1920×550 canvas geometry;
- 68 physical key rectangles;
- native index, stable ID, label, and USB usage reference;
- display-safe blank regions;
- a four-pixel right-edge overscan correction.

The key layout was physically checked across the board. Content at the far right
may intentionally clip a few pixels because the calibrated 18U footprint is
slightly wider than the visible viewport.

## Release invariant

Always process release edges even when a mode is Ready or Paused. If a state
change gates the release path, a key light can remain visually latched.
Keyfield A2 gates new press effects to Live but allows every release through.
