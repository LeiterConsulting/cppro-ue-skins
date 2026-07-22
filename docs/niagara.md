# Niagara on the Centerpiece Pro

Niagara is confirmed on the tested Centerpiece Pro runtime using UE4.27
Android ASTC content.

## Confirmed system matrix

All of the following rendered and remained stable on-device:

- CPU simulation with normal age updates;
- CPU simulation held at a desired age;
- CPU solo components;
- CPU systems with an alternate particle material;
- GPU simulation with normal age updates;
- GPU simulation held at a desired age; and
- a direct, unmodified UE4.27 stock Niagara system.

This confirms the technology surface, not every possible module, renderer, or
material configuration.

## The world/UMG composition rule

Niagara renders in the world scene. Viewport UMG renders over that scene.
Consequently, an opaque full-screen UMG background can produce a perfectly
stable black field while Niagara continues to load, simulate, and report
active behind it.

Use one of these layouts:

1. A transparent full-screen UMG root with small opaque HUD panels.
2. A world-only particle scene with no full-screen UMG fill.
3. A deliberately masked UMG composition whose transparent window exposes the
   world layer.

When diagnosing a missing effect, place an ordinary world mesh at the Niagara
component's transform. If the mesh is visible but particles are not, inspect
the system, renderer, material, bounds, scale, and age state. If neither is
visible, inspect the active camera and UMG occlusion first.

## Bounded component pattern

Prefer a fixed pool:

```text
startup
  -> create or expose a bounded component pool
  -> assign systems and fixed transforms
  -> keep unused components hidden or inactive

key event
  -> select an existing component
  -> move it to the calibrated key position
  -> set parameters
  -> reinitialize
```

This avoids runtime allocation spikes and makes the maximum workload explicit.

## Measured GPU stress curves

The diagnostic used 64 preallocated GPU Niagara components. Each component
held the same duplicated UE4.27 burst system at a representative desired age.
Eight additional systems were exposed per scene. The safe-region HUD recorded
the minimum integer FPS observed for each scene.

The first broad sweep included each scene's activation transient:

| Active systems | Minimum FPS |
| ---: | ---: |
| 0 | 29 |
| 8 | 29 |
| 16 | 29 |
| 24 | 18 |
| 32 | 14 |
| 40 | 11 |
| 48 | 9 |
| 56 | 8 |
| 64 | 7 |

A second sweep isolated the knee. Each scene was allowed to warm for two
seconds; only then was the LOW counter reset and allowed to record sustained
performance:

| Active systems | Sustained minimum FPS |
| ---: | ---: |
| 16 | 29 |
| 18 | 26 |
| 20 | 21 |
| 22 | 18 |
| 24 | 18 |
| 26 | 17 |
| 28 | 15 |
| 30 | 15 |
| 32 | 14 |

For this exact system, 16 simultaneous held components maintain the runtime's
approximately 29 FPS ceiling. Eighteen remain close to that ceiling, 20 reach
21 FPS, and the sustained result falls below 20 FPS at 22 components. Choose a
pool size from the frame-rate requirement rather than the largest stable
count.

Reset performance counters after a short warm-up. Otherwise the result mixes
the one-time cost of revealing and activating components with their sustained
simulation and rendering cost.

These values are not a universal particle limit: emitter count, sprites per
emitter, overdraw, material complexity, bounds, simulation target, and age
behavior all affect cost.

## Design controlled benchmarks

Do not treat a duplicated multi-emitter template as a particle-count control.
The stock UE4.27 `SimpleExplosion` template contains three independent
emitters with different renderers and burst counts. Duplicating the complete
template changes emitter count, particle count, renderer mix, random state,
and shader workload at the same time.

For a particle-density benchmark:

- keep the Niagara component count fixed;
- keep one emitter and renderer configuration fixed;
- enable emitter determinism and use a fixed seed;
- change only the serialized spawn count;
- allow activation and system swapping to settle; and
- reset minimum-FPS telemetry after that warm-up.

Use whole-system or whole-emitter duplication only when the intended question
is aggregate load or pooling stability.

### Deterministic sprite-count curve

A controlled follow-up used 16 fixed GPU Niagara components. Each system kept
only one enabled deterministic `SimpleSpriteBurst` emitter and used the same
sprite renderer, material, desired age, bounds, seed, and transforms. Only the
serialized spawn count changed. LOW was reset after a two-second warm-up.

| Particles per system | Requested sprites across 16 systems | Sustained minimum FPS |
| ---: | ---: | ---: |
| 10 | 160 | 29 |
| 25 | 400 | 29 |
| 50 | 800 | 29 |
| 100 | 1,600 | 29 |
| 200 | 3,200 | 29 |
| 400 | 6,400 | 24 |
| 800 | 12,800 | 13 |

For this exact renderer and material, 3,200 requested sprites remain at the
device's approximately 29 FPS ceiling. A 6,400-sprite scene is viable at
24 FPS, while 12,800 is outside a useful interactive budget at 13 FPS.

Treat 3,200 as a measured starting budget, not a device-wide guarantee.
Translucent overdraw, sprite size, lifetime, forces, collision, material
complexity, and screen coverage can move the knee substantially.

## Packaging checklist

- Author and cook with UE4.27.
- Target Android ASTC.
- Include the Niagara system, emitters, materials, textures, and cooked shader
  data reachable from the canonical map.
- Keep the entry map at `/Game/map/M_EntryPoint`.
- Do not place an opaque full-screen UMG fill over the world layer.
- Use fixed-size pools and explicit bounds.
- Record PAK integrity and SHA-256 before uploading.
- Test new Niagara modules or large load increases in a nonessential slot.
