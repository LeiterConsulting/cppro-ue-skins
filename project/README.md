# UE4.27 project

This is the minimal editable `spark` project used by the CPPRO runtime.

Included content:

- `/Game/map/M_EntryPoint` — canonical startup map.
- `/Game/CPPRO/KeyfieldA2/BP_KeyfieldA2` — input and app-state actor.
- `/Game/CPPRO/KeyfieldA2/WBP_KeyfieldA2` — calibrated display widget.
- `Plugins/SkinApi` — clean-room authoring/cook stub.

The stub lets UE4.27 resolve the Blueprint API while authoring. The keyboard is
expected to provide the actual SkinApi runtime implementation. Most geometry
helper functions in the local stub deliberately return neutral values; they are
declarations for cooking, not a desktop emulation of the hardware.

Do not rename the project module or canonical map during initial work. Duplicate
the A2 actor and widget, edit the copies, and replace the actor in the canonical
map.

Generated folders are ignored by the repository. Unreal Engine itself is not
redistributed.
