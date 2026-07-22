# Authoring guide

## Design for the physical display

The screen is 1920×550 beneath the switches. Fine text is difficult to read
under keycaps even though the display is high resolution. Use large ambient
forms under keys and reserve dense status information for the blank regions
defined in `layout/cppro-key-layout-v1.json`:

- `h_rail`
- `h_shelf`
- `h_right_leg`
- `right_ctrl_left_arrow_gap`

The SVG preview renders these regions and every key footprint.

## Use native layout indices

The event callback's `HCode` is the native layout index `0..67` on the tested
runtime. It is not a USB usage ID. Resolve it directly through
`keys[].layout_index`. The layout JSON also includes USB usages for host-side
reference, but those values must not drive the skin callback mapping.

## Treat actuation as binary

`IsActuated` reliably distinguishes press and release. Although the ABI includes
an integer `Percentage`, the tested runtime supplies 100 on presses rather than
continuous analog travel. Host-side USB capture can observe analog movement,
but the tested Android SkinApi does not forward that resolution to the skin.
Avoid device-resident gameplay that depends on pressure depth.

Useful device-local substitutes include:

- elapsed time between the press and release edges;
- recent key-event cadence;
- per-key usage counters and decaying energy;
- chord state; and
- persistent profile or mode state.

## Keep effects bounded

The keyboard is a constrained runtime. Prefer:

- preallocated widgets or actors;
- fixed-size pools;
- short deterministic timelines;
- recycling the oldest visual when a pool fills;
- a release path that always clears held state;
- one new runtime technology per hardware experiment.

Avoid unbounded spawning, large textures, excessive translucency, tick-heavy
graphs, or state transitions that discard release events.

## Compose UMG and Niagara deliberately

Niagara is confirmed on the tested device for both CPU and GPU simulation. It
renders through the world camera; viewport UMG is composited over it. An opaque
1920×550 UMG background therefore hides the entire particle scene even while
every Niagara component reports loaded, assigned, and active.

For a hybrid particle skin:

- keep the full-screen UMG world window transparent;
- use opaque UMG only for intentional HUD or safe-region panels;
- preallocate a fixed Niagara component pool;
- move and reinitialize pooled components instead of spawning per keypress;
- set explicit fixed bounds where appropriate;
- cook particle shaders for Android ASTC; and
- measure the actual emitter/material combination on the keyboard.

The held-system benchmark remained at the device's approximately 29 FPS ceiling
through 16 GPU systems. A two-second warm-up sweep measured 26 FPS at 18
systems, 21 FPS at 20, and 18 FPS at 22. Reset performance counters after
activation settles so the one-time reveal cost is not mistaken for sustained
rendering cost. This is evidence for bounded pooling, not a universal
particle-count limit. See [Niagara](niagara.md) for the complete measured
curves and integration checklist.

## Use a hybrid scene when physics helps

The Koi Pond example separates simulation from presentation. Small invisible
world actors provide collision, steering, separation, and key impulses; UMG
images provide the full-resolution pond and animated koi. Each tick maps a
physics proxy into the 1920×550 widget and applies a bounded turn rate to its
sprite.

This is useful when a skin needs moving actors but late-mounted custom material
shaders are unreliable. Keep the world actor count fixed, share animation
textures across actors, preallocate reactive widgets, and avoid spawning on
keypress. See the [Koi Pond architecture](../examples/koi-pond/ARCHITECTURE.md)
for the complete pattern.

## Separate controls from visuals

Use stable physical IDs such as `enter`, `tab`, and `arrow_left` in profiles.
Resolve them to native indices through the layout. Keep state and control logic
outside individual effect widgets so a theme or effect can change without
rewiring the application shell.

## Designer manifests

The current manifest surface validates:

- identity and 1920×550 canvas;
- layout, profile, and theme references;
- allowed app states;
- bounded key-light, release-pad, and wave pools;
- named palettes and semantic controls.

`cppro_skin_kit.py lock` records the exact input hashes. The manifest is not yet
a general Blueprint compiler; runtime changes still happen in the included
UE4.27 assets.
