# Koi Pond architecture

## Design goal

The scene should remain alive without input, react at the exact position of any
key, and look like one continuous pond beneath the switch plate. It must also
stay bounded on the keyboard's constrained UE4.27 Android runtime.

The implementation therefore uses a hybrid model:

- the physics world owns movement, collision, separation, and impulses;
- UMG owns the high-resolution pond, koi artwork, and water ripples;
- one actor synchronizes the two layers and receives SkinApi input.

This avoids depending on custom late-mounted material shaders for the primary
art while retaining Unreal's mature physics operations.

## Presentation layers

The widget uses the confirmed 1920×550 logical canvas.

| Z order | Layer | Count | Role |
| --- | --- | ---: | --- |
| 0 | Pond image | 1 | Opaque, full-viewport underwater artwork |
| 2 | Koi images | 6 | True-alpha animated sprites |
| 4 | Ripple rings | 204 | Three preallocated stages for each of 68 keys |

The pond is anchored to all four viewport edges. Its offsets extend 16 px past
the left and right and 8 px past the top and bottom. This crop-safe bleed
absorbs physical-display and viewport rounding instead of exposing the
device-resident world layer as a bright seam.

All diagnostic text, key outlines, legacy lights, and key-free-region panels are
collapsed for this visual example.

## Input path

The actor binds to:

```text
GetKeyEventReceiver()
  -> OnKeyEvent(HCode, IsActuated, Percentage)
```

`HCode` is resolved directly as the physically validated layout index `0..67`.
It is not interpreted as a USB usage ID.

For each press:

1. Resolve the key footprint from the calibrated layout.
2. Use the footprint center as the screen interaction position.
3. Convert the screen position into pond-world coordinates.
4. Show the three preallocated ring widgets for that key.
5. Sphere-trace vertically through the pond near the interaction point.
6. If a fish proxy is hit, apply a radial impulse to that component.

Release routing is retained so held state cannot latch, even though the visible
pond reaction begins on press.

The trace radius is 130 world units. The local impulse uses a 210-unit radius,
6,500 strength, linear falloff, and no velocity-change override.

## Fish representation

Each fish has two representations:

- a small world `StaticMeshActor` used as a physics proxy;
- a UMG `Image` used as the visible koi.

Six proxies are tagged `CPPROPoolMover`. Their visual sizes range from 119×60
to 192×96 px so the school has depth and variety. The physics bodies never
render as the final fish artwork.

Every tick, the controller:

1. retrieves the six tagged movers;
2. advances steering and recovery;
3. converts each world position to a UMG canvas position;
4. computes a desired visual heading;
5. turn-limits the current heading;
6. selects the shared animation frame only when the frame index changes.

The calibrated world-to-screen scale is:

```text
screen_x = 960 - world_x * 1.021276596
screen_y = 275 - world_y * 1.057692308
```

## Continuous swimming

Each fish receives its own cruise speed, steering gain, waypoint rate, phase,
stall threshold, and recovery impulse. The controller combines:

- a forward cruise term;
- a time-varying waypoint target;
- arrival scaling as the fish approaches that target;
- velocity feedback;
- boundary containment;
- local fish-to-fish separation;
- a low-speed recovery impulse.

Waypoint targets cover approximately ±700 world units horizontally and ±190
vertically. Different irrational angular steps and per-fish phases prevent the
school from sharing one repeating route.

The visible heading follows the desired direction at no more than 105 degrees
per second. Below an 18-unit movement threshold, the sprite retains its previous
heading. This commitment rule prevents rapid about-faces when the steering
solution is nearly stationary or momentarily ambiguous.

Physics boundaries extend beyond the intended visible travel area so sprites
may turn naturally while partly leaving the display instead of appearing
pressed against an invisible wall. Separation forces reduce grouping without
requiring pairwise Blueprint spawning or dynamic controller objects.

## Animation

The original atlas contains eight cruise poses in its first row. Offline
motion-compensated interpolation produces 16 shared runtime frames. The actor
advances them at 10 frames per second, creating a 1.6-second cycle. Each fish
uses a different phase offset.

Frames are shared textures; the skin does not allocate a separate animation set
for every fish. Texture changes occur only when the integer frame changes.

The atlas's second row is reserved for a stronger turn or reaction sequence.
It is intentionally excluded from ordinary cruising so the fish do not appear
to snap into a hard bend every cycle.

## Fixed runtime budget

The example keeps its major resources bounded:

- 6 fish proxies;
- 6 koi image widgets;
- 16 shared 256×128 cruise textures;
- 68 key interaction routes;
- 204 ripple widgets;
- 1 pond background.

Nothing is spawned by a keypress. A press activates already-created visual
stages and applies an impulse to an existing component.

## Tuning guide

Change one family at a time:

| Desired result | Primary parameters |
| --- | --- |
| Faster roaming | Cruise speed |
| Stronger destination commitment | Steering gain and waypoint duration |
| Wider exploration | Waypoint X/Y amplitude |
| Fewer clusters | Separation radius and force |
| Less edge dwelling | Boundary force and offscreen margin |
| Fewer low-speed pauses | Stall threshold and recovery impulse |
| Softer visual turns | Heading turn rate |
| Less heading chatter | Heading-active threshold |
| Faster tail motion | Animation frame rate |
| Larger key response | Ripple diameters and impulse radius |

Preserve preallocation, the canonical map path, native layout-index routing,
and the separation between physics proxies and UMG presentation.
