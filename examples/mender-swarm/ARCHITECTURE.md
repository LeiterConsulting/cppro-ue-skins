# Mender Swarm architecture

## Design goal

Mender Swarm makes input look consequential without becoming a conventional
game. The keyboard is a living synthetic surface, key presses damage it, and
small maintenance machines continually keep it intact.

The release is deliberately bounded for the CPPRO's UE4.27 Android runtime:

- one opaque 1920×550 base image;
- two sparse transparent flow layers;
- twelve invisible physics proxies;
- twelve UMG presentation sprites;
- four preallocated damage images;
- four fixed work records;
- no per-press allocation or unbounded event history.

## Runtime layers

| Layer | Role |
| --- | --- |
| `BP_MenderSwarmA1` | Receives key events, stores four work records, updates physics, and drives presentation |
| Invisible mesh proxies | Supply collision, velocity, separation, and localized impact response |
| `WBP_MenderSwarmA1` | Renders the substrate, flow layers, menders, damage, and Caps state |
| Original texture set | Supplies the full-screen fabric, sparse motion, damage mark, and state animation |
| Canonical entry map | Starts the experience through `/Game/map/M_EntryPoint` |

The physics bodies are intentionally hidden. Their calibrated world positions
are projected into the 1920×550 widget, where the original sprites can remain
crisp and unlit beneath the physical keycaps.

## Input and privacy

The actor binds to:

```text
GetKeyEventReceiver()
  -> OnKeyEvent(HCode, IsActuated, Percentage)
```

`HCode` is the physically confirmed CPPRO native index `0..67`, not a USB
usage ID. The skin does not reconstruct text, log words, write files, use the
network, or receive the host application's composed characters.

Each press maps the calibrated key center into both:

- widget coordinates for the visible damage image; and
- world coordinates for the local physics trace and work destination.

Releases do not destroy the damage mark. Each mark has its own expiry time.

## Four-channel repair model

The release stores four fixed work records:

```text
MenderWorkX0..3
MenderWorkY0..3
MenderWorkUntil0..3
```

A key selects a channel with `HCode mod 4`. The channel receives the new
position and an expiry approximately 6.5 seconds in the future. Its damage
image is moved to that key and fades as the expiry approaches.

The twelve menders are divided into four stable crews:

| Crew | Members | Work channel |
| --- | --- | ---: |
| 0 | 0, 4, 8 | 0 |
| 1 | 1, 5, 9 | 1 |
| 2 | 2, 6, 10 | 2 |
| 3 | 3, 7, 11 | 3 |

Within each crew, target commitment is weighted `1.00`, `0.82`, and `0.65`.
The first responder converges most directly, while the other two retain more
of their current patrol trajectory. This produces a small repair gathering
without making every agent move as one rigid group.

This is a bounded approximation of a dynamic job scheduler. It provides four
simultaneous visible jobs with predictable cost and no Blueprint array
mutation during rapid typing.

## Steering and motion

At idle, every mender follows its own slow, phase-shifted exploration target.
The targets traverse broad horizontal and vertical ranges so agents do not
settle into corners or a shared gravity well.

While a crew's work record is active, its exploration target is blended toward
the damage location. Arrival speed is capped so menders approach rather than
oscillating violently across the wound.

Additional controls keep the presentation stable:

- gravity is disabled;
- vertical translation and off-plane rotation are locked;
- linear and angular damping suppress collision chatter;
- a low-speed recovery impulse prevents permanent settling;
- soft limits and physical walls keep agents inside a small display bleed;
- key impacts use a short inward radial impulse rather than launching agents
  away from the job.

## Presentation and animation

The original source atlas contains five authored postures: patrol, startled,
travel, repair, and recover. The artwork generator produces sixteen
presentation frames:

- frames `0..2`: warm repair/recover;
- frames `3..7`: cool patrol/travel;
- frames `8..15`: magenta startled response.

Tiny authored bob offsets add continuity without fabricating opaque
interpolated states. Whole-body orientation comes from the actor's smoothed
heading, not from separate directional sprite sets.

The full substrate is static. Continuous environmental movement comes from
two oversized transparent flow textures whose UMG positions move smoothly at
different rates and phases. This avoids the low apparent frame rate observed
when large full-screen bitmap frames were swapped.

## Caps indicator

Caps Lock uses native index `32`. A press-edge latch toggles a session-local
state once per physical press and renders a thematic tint beneath the physical
Caps key.

The callback cannot read the host operating system's initial Caps state or
composed `a` versus `A`. The indicator therefore begins off when the skin
loads and tracks Caps presses received during the session.

## Performance and limits

The device was observed near its usual 29 FPS ceiling during normal use. The
runtime cost is fixed: twelve movers, four damage fades, two substrate
transforms, and twelve presentation updates per tick.

Current intentional limits:

- at most four damage sites are retained;
- a new press can replace an older job in the same modulo channel;
- damage fades on time rather than measuring exact worker arrival;
- menders visually converge but do not yet deform the substrate around their
  individual tools;
- continuous analog key depth is unavailable because the callback reports
  `Percentage=100` for every press.

These limits are useful extension points: a future version could add a bounded
priority queue, worker-arrival-controlled repair progress, reinforcement
memory, or local filament effects while preserving the same fixed-cost model.
