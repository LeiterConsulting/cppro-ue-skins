# Getting started

## 1. Install UE4.27

Install Unreal Engine 4.27 and its Android support. The device build uses the
Android ASTC cook target. Confirm that this executable exists:

```text
<UE4.27>\Engine\Binaries\Win64\UE4Editor-Cmd.exe
```

`UnrealPak.exe` must also exist under the same engine root.

## 2. Open the project

Open `project/spark.uproject`. If Unreal asks to rebuild modules, allow it. The
project's module and plugin are authoring-time stubs; the keyboard provides its
own SkinApi implementation at runtime.

The startup map is `/Game/map/M_EntryPoint`. Do not rename or move this map in
your first experiments.

The checked-in map launches Keyfield A2. Examples that need their own world
actors may include an exact canonical map snapshot. Koi Pond documents how to
activate its snapshot, cook it, and restore the default map.

## 3. Run the example locally

Play-in-editor can exercise visuals and Blueprint structure, but a desktop
editor cannot reproduce the keyboard's real SkinApi event source. Use the
dependency-free reference runtime to check state/profile semantics:

```powershell
python -m unittest discover -s reference/runtime -v
```

## 4. Make a new skin

1. Duplicate `/Game/CPPRO/KeyfieldA2/BP_KeyfieldA2`.
2. Duplicate `/Game/CPPRO/KeyfieldA2/WBP_KeyfieldA2`.
3. Give both copies a unique folder and name.
4. Point the actor's widget class at your widget copy.
5. Replace the actor in `/Game/map/M_EntryPoint`.
6. Keep the effect count bounded and reuse objects instead of spawning forever.
7. Copy `examples/keyfield-a2/manifest` and update its identity, theme, controls,
   and declared pool limits.
8. Validate and preview the manifest before cooking.

## 5. Build and inspect

Use `tools/build-pak.ps1`. It compiles the editor target, cooks only the
canonical map for Android ASTC, stages the required `Engine/` and `spark/`
layout, builds a version-11 PAK with mount point `../../../`, tests it, and
prints its SHA-256.

The build never communicates with the keyboard. Installation is a separate,
explicit `--send` operation.
