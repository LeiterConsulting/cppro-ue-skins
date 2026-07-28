# Circuit Stunt Show architecture

## Design goal

Circuit Stunt Show is a kinetic arena that remains active at idle and turns
typing into several concurrent destinations. Its behavior is deliberately
bounded so rapid input cannot create an unbounded number of actors, widgets,
or work records.

## Runtime composition

| Layer | Role |
| --- | --- |
| `BP_MenderSwarmA1` | Receives input, stores four stunt sites, updates physics, and drives presentation |
| Twelve hidden mesh proxies | Supply rider motion, collision, separation, and recovery |
| `WBP_MenderSwarmA1` | Renders the arena, current layers, riders, site markers, and Caps state |
| Original texture set | Supplies circuit artwork and sixteen rider states |
| `/Game/map/M_EntryPoint` | Canonical device entry |

The widget renders the original unlit art. Hidden physics bodies determine
rider position and smoothed heading.

## Input and site allocation

`OnKeyEvent(HCode, IsActuated, Percentage)` supplies confirmed native key index
`0..67`. Each index maps to the calibrated physical key center. Its value
modulo four selects one fixed site record and one stable crew of three riders.

Four landing or repair sites can coexist. A new press replaces only the older
site in the same channel, keeping cost constant even during very fast typing.
The controller uses key position and event timing only; it does not reconstruct
text or communicate outside the skin.

## Steering and animation

At idle, riders follow broad phase-shifted exploration targets. When a site is
active, its crew blends toward the key coordinate with three commitment
strengths, creating a lead rider and two looser responders. Damping, disabled
gravity, low-speed recovery, soft boundaries, and display bleed prevent
settling and obvious invisible-wall impacts.

The static arena costs one opaque draw layer. Two sparse oversized overlays
translate to create flowing current and sparks. Runtime cost remains fixed at
twelve movers, four markers, two background transforms, and twelve sprite
updates per tick.

## Caps state and input limits

Native Caps index `32` toggles a session-local Boolean on its press edge. It
cannot discover the host operating system's initial lock state and therefore
starts off. The installed UE callback also reports `Percentage=100` for all
presses, so true analog depth is unavailable in this skin.
