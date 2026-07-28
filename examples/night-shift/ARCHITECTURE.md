# Night Shift architecture

## Design goal

Night Shift is an ambient miniature city rather than a start-and-finish game.
It should read as active before the first key press, react locally to typing,
and retain several visible consequences without allowing event history or
actor counts to grow without bound.

## Runtime layers

| Layer | Role |
| --- | --- |
| `BP_MenderSwarmA1` | Receives key events, stores four service calls, updates physics, and drives presentation |
| Twelve hidden mesh proxies | Provide collision, velocity, separation, recovery, and input impulses |
| `WBP_MenderSwarmA1` | Renders the city, parallax traffic, service beacons, craft, and Caps state |
| Original texture set | Supplies the full-screen skyline and sixteen craft states |
| `/Game/map/M_EntryPoint` | Canonical device entry map |

The service-craft images are UMG presentation sprites. Hidden physics bodies
supply their position and heading, keeping the original artwork crisp and
unlit while preserving collision and steering.

## Input routing

The actor binds to:

```text
GetKeyEventReceiver()
  -> OnKeyEvent(HCode, IsActuated, Percentage)
```

`HCode` is the confirmed CPPRO native index `0..67`. Each press maps its
calibrated center to widget coordinates for the beacon and to world coordinates
for the responding crew. The skin does not reconstruct text, write files, use
the network, or receive host-composed characters.

## Fixed four-call model

Four preallocated service records retain positions and expiry times. Native key
index `HCode mod 4` selects one record. The twelve craft form four stable crews
of three, so four separated key regions can remain visibly active at once.

This intentionally bounded model avoids per-press object creation and an
unbounded queue during fast typing. A new call replaces only the older call in
the same channel.

## Motion and performance

Craft follow independent phase-shifted patrol targets at idle. Active crews
blend their target toward the selected key, then resume patrol after repair.
Gravity is disabled, damping suppresses chatter, soft bounds include display
bleed, and low-speed recovery prevents permanent settling.

The background is one opaque image. Two sparse 2000×590 overlays translate
smoothly at different rates to create traffic and window motion without
swapping full-screen frames. Runtime cost remains fixed: twelve movers, four
beacons, two parallax transforms, and twelve sprite updates per tick.

## Caps state and limits

Caps Lock is native index `32`. A press-edge latch toggles a session-local
Boolean and tints the physical Caps region. The callback cannot read the host
operating system's initial lock state, so the indicator begins off when the
skin loads.

Continuous analog travel is also unavailable to this runtime: confirmed
callbacks report `Percentage=100` for every press.
