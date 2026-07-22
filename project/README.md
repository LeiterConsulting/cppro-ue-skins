# UE4.27 project

This is the minimal editable `spark` project used by the CPPRO runtime.

Included content:

- `/Game/map/M_EntryPoint` — canonical startup map.
- `/Game/CPPRO/KeyfieldA2/BP_KeyfieldA2` — input and app-state actor.
- `/Game/CPPRO/KeyfieldA2/WBP_KeyfieldA2` — calibrated display widget.
- `/Game/CPPRO/KeyfieldPulse/BP_KeyfieldPulse` — always-live input,
  release-wave, and Caps-state actor.
- `/Game/CPPRO/KeyfieldPulse/WBP_KeyfieldPulse` — clean daily-use keyfield
  widget with all calibration chrome removed.
- `/Game/CPPRO/TouchPoolL1/BP_TouchPoolL1` — Koi Pond input, physics,
  steering, and presentation actor.
- `/Game/CPPRO/TouchPoolL1/WBP_TouchPoolL1` — Koi Pond scene widget.
- `/Game/Game/Physics/PM_CPPRO_Lively` — shared physical-material settings
  used by the pond proxies.
- `Plugins/SkinApi` — clean-room authoring/cook stub.

The stub lets UE4.27 resolve the Blueprint API while authoring. The keyboard is
expected to provide the actual SkinApi runtime implementation. Most geometry
helper functions in the local stub deliberately return neutral values; they are
declarations for cooking, not a desktop emulation of the hardware.

Do not rename the project module or canonical map during initial work. Duplicate
the A2 actor and widget, edit the copies, and replace the actor in the canonical
map.

The checked-in canonical map launches Keyfield A2. Other complete skins include
their exact canonical map snapshots under their `examples/*/project-map/`
folders; follow the selected example's README to activate it before cooking.

Generated folders are ignored by the repository. Unreal Engine itself is not
redistributed.
