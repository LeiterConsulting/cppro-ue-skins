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
continuous analog travel. Avoid gameplay that depends on pressure depth.

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
