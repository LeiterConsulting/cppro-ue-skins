# Midnight Conveyor architecture

## Design goal

Midnight Conveyor presents a continuously operating miniature factory. Input
adds visible work without stopping the ambient machinery or making every agent
chase the latest press.

## Runtime composition

| Layer | Role |
| --- | --- |
| `BP_MenderSwarmA1` | Routes input, stores four parcel jobs, updates bot physics, and drives the widget |
| Twelve hidden mesh proxies | Supply motion, collision, separation, and recovery |
| `WBP_MenderSwarmA1` | Renders belts, parcels, bots, work markers, and Caps state |
| Original texture set | Supplies the factory, two moving overlays, and sixteen bot states |
| `/Game/map/M_EntryPoint` | Canonical entry map |

The physical proxies remain invisible. Their coordinates and headings drive
crisp UMG sprites under the keybed.

## Input and bounded jobs

The controller receives `OnKeyEvent(HCode, IsActuated, Percentage)` from the
SkinApi receiver. Confirmed native index `0..67` selects the physical key
center. The index modulo four chooses one preallocated parcel channel; one
stable three-bot crew serves each channel.

Four jobs can coexist. A fifth does not allocate more state: it replaces only
the previous job in its channel. This keeps rapid typing predictable and
prevents a queue from growing indefinitely.

The skin processes positions and timing only. It does not reconstruct typed
text, log input, access files, or use the network.

## Continuous motion

The opaque factory base is static. Two sparse 2000×590 overlays translate
smoothly, making belt arrows and parcels move without swapping expensive
full-screen images. Bots retain independent phase-shifted idle targets and
blend toward an active parcel while their channel is live.

Gravity is disabled. Damping, soft boundaries, low-speed recovery, and
display-edge bleed prevent settling and avoid visible invisible-wall impacts.
The cost is fixed at twelve movers, four job markers, two background
transforms, and twelve presentation updates.

## State limitations

Caps Lock native index `32` toggles a session-local press-edge latch. The skin
cannot read the host operating system's initial Caps state, so it begins off.
The runtime also reports `Percentage=100` on every press, preventing continuous
analog-depth effects inside the skin.
