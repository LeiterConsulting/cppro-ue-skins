# Moodfield architecture

## Design goal

Moodfield turns the entire 1920×550 CPPRO panel into one continuous responsive
surface. A key press should feel like pressure applied to that surface, while
longer behavior—typing, repetition, focused controls, pauses, and changes of
region—should establish a visible mood that outlives any one press.

The implementation is bounded for the keyboard's UE4.27 Android runtime:

- one opaque full-screen UI material;
- one Material Parameter Collection (MPC);
- one fixed Blueprint input/classifier graph;
- three recent-contact records;
- six slow alpha-zone memories;
- no per-press widget, actor, particle, or texture allocation.

The surface is generated mathematically and requires no bitmap artwork.

## Runtime layers

| Layer | Role |
| --- | --- |
| Keyfield Pulse actor | Receives `OnKeyEvent`, retains Caps state, and owns the fixed classifier variables |
| Moodfield Blueprint bridge | Converts press edges and rolling usage into MPC scalar parameters |
| `MPC_Moodfield` | Stable boundary between Blueprint state and the display material |
| `M_MoodfieldSurface` | Renders the substrate, contacts, paths, basins, modes, and Caps tint |
| Canonical entry map | Starts the actor through `/Game/map/M_EntryPoint` |

The release and repository generator use the proven Keyfield Pulse actor
package path because Unreal references inside cooked assets are path-sensitive.
Run the generator in a branch or disposable checkout; the exact pre-generated
overlay is included when direct inspection is preferable.

## Input and privacy model

The actor binds to:

```text
GetKeyEventReceiver()
  -> OnKeyEvent(HCode, IsActuated, Percentage)
```

`HCode` is the physically confirmed CPPRO layout index `0..67`. It is not a USB
usage ID. The skin processes numeric key categories and timing only. It does
not reconstruct words, log text, write files, use the network, or receive the
character produced by the host application.

The installed device runtime reports `Percentage=100` for each press, so
Moodfield derives expression from press/release edges, hold duration, interval,
cadence, repetition, recent travel, and rolling usage. Continuous analog depth
is not used.

## Classifier memories

Every press updates fixed scalar memories:

| Memory | Purpose |
| --- | --- |
| Event interval | Distinguishes isolated input from sustained cadence |
| Burst and repeat | Adds short-lived urgency and repeated-key texture |
| Three recent contacts | Draws local pressure, rebound, and travel paths |
| Left/center/right mass | Detects sustained concentration in broad regions |
| WASD share | Gives a proven gaming pattern immediate visual authority |
| Navigation share | Recognizes arrow/navigation-heavy behavior |
| Alpha left/right share | Separates bilateral prose from unilateral control clusters |
| Six alpha zones | Builds top/middle/bottom × left/right typing geography |

The six-zone system intentionally covers the three alpha rows. The number row
still produces localized contact and contributes to general activity, but it
does not currently reshape the prose basin.

## Pattern modes

Moodfield does not use a single hard-coded WASD effect as its whole model.

- Ordinary typing builds a weighted basin from the six alpha-zone memories.
- Repeated words and row-biased typing move and resize that basin.
- Any sustained compact control group raises regional concentration.
- WASD gets an additional fast path because it is a common, unambiguous game
  pattern.
- Arrow-heavy input receives secondary navigation weighting.
- Returning to broad bilateral typing releases focused modes back into the
  general substrate.

The detector chooses visual ownership; it does not suppress exact localized
contact beneath the key that was pressed.

On release hardware, the dedicated WASD response is immediately evident while
arrow weighting remains subtle and may not read as a separate mode. Arrow keys
still produce correctly localized contact. This is a documented tuning limit,
not a claim of equivalent visual strength.

## Surface lifecycle

The release surface has three visual phases:

1. **Active:** rapid input warms the basin core toward amber and orange while
   pressure rims and paths remain teal/cyan.
2. **Retained:** after input stops, the accumulated shape holds at full
   authority for about 3.5 seconds.
3. **Afterglow:** the basin cools toward violet and deep blue while fading over
   roughly 29 additional seconds.

After a long pause, one new key only begins to wake the retained map. A short
three-contact sequence restores full authority. This prevents stale geography
from flashing back at maximum intensity while keeping resumed typing
responsive.

The basin centroid and radius come from the weighted six-zone distribution.
Low-frequency substrate currents perturb only its edge, so the field breathes
without drifting away from the user's accumulated region.

## Caps indicator

Caps Lock uses native index/HCode `32`. A separate press-edge latch toggles a
session-local integer state once per physical press. The active state appears
as a warm tint beneath the physical Caps Lock key.

The runtime callback does not expose the host operating system's Caps Lock
state or composed characters. The indicator therefore starts off when the skin
loads and tracks presses received during that skin session.

## Performance model

The material uses three low-frequency sine evaluations for the full substrate.
All other shapes are built from arithmetic, distance fields, and the fixed MPC
inputs. No Niagara system, render target, dynamic texture, or unbounded pool is
required.

This keeps the surface near the CPPRO's observed 29 FPS ceiling while allowing
multiple simultaneous memories and exact per-key contact.

## Authoring and generation

The canonical source is:

| Path | Purpose |
| --- | --- |
| `tools/ue-moodfield-build.py` | Defines MPC parameters and generates the complete UI material |
| `project/Source/spark/MoodfieldAuthoringLibrary.*` | Builds and validates the Blueprint classifier/bridge |
| `project/Content/CPPRO/Moodfield/Materials/` | Editable generated material and MPC assets |
| `examples/moodfield/project-overlay/` | Exact actor/widget assets used by the release PAK |
| `examples/moodfield/project-map/` | Exact canonical release map |

The generator is idempotent: it rebuilds the generated material, applies the
bridge to a working copy of Keyfield Pulse, preserves stable object paths,
compiles the Blueprint, and executes an event-driven self-test before saving.

## Tuning guide

| Desired result | Primary area |
| --- | --- |
| Longer or shorter retained mood | `moodPersistence` in the surface material source |
| Faster re-entry after a pause | `sequenceDepth` and `moodReengagement` |
| Warmer active typing | `proseBasinActiveColor` |
| Cooler or brighter decay | `proseBasinRestColor` and `proseBasinHalo` |
| Wider prose geography | Basin variance multipliers |
| Faster regional migration | Six-zone retention/sample weights in `AddProseZoneBridge` |
| Stronger generalized clusters | Concentration and `clusterEvidence` thresholds |
| Stronger dedicated WASD mode | `gameEvidence` and `wasdField` |

Change one family at a time and verify normal typing, a repeated word, a
compact non-WASD cluster, WASD, arrows, Caps Lock, multi-key holds, and a pause
followed by resumed typing.
