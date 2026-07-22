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

This is a runtime delivery limitation, not evidence that the keyboard lacks
analog sensing. Continuous travel values are observable in host-side USB
traffic, while the tested Android Unreal callback remains effectively binary.
Keep host integrations and device-resident skin capabilities documented as
separate data paths.

The `SkinApi` plugin in `project/Plugins` is a cook-time clean-room declaration.
The device supplies the real runtime module.

## Lock-key state

The confirmed callback reports physical key activity only. It does not expose:

- the host operating system's Caps Lock state or keyboard LED report;
- composed text or characters such as `a` versus `A`;
- enough information for a skin to infer capitalization after the host applies
  Shift, Caps Lock, keyboard layout, IME, or application-specific processing.

A device-resident skin can still provide a useful **session-local** Caps Lock
indicator: initialize an internal Boolean to off, then toggle it on each Caps
Lock press edge while ignoring the release edge. This stays correct when the
skin starts with host Caps Lock off and Caps Lock is only changed through the
keyboard while that skin remains loaded. Its initial state is unknown if the
skin loads while host Caps Lock is already on, and it cannot correct itself by
observing typed letters because those letters are not delivered to the skin.

Authoritative synchronization requires a separate host bridge, an exposed HID
LED/status path, or a future plugin API that reports the host lock state.

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
