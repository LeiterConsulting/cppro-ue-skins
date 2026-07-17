# SkinApi authoring stub

The CPPRO device supplies a runtime module named `/Script/SkinApi`. UE4.27 needs
matching declarations while editing and cooking Blueprints, so this repository
provides a small clean-room stub.

Confirmed and used by Keyfield A2:

```text
GetKeyEventReceiver()
OnKeyEvent(HCode: byte, IsActuated: bool, Percentage: int32)
```

Additional geometry/mapping declarations are included for future original
skins. Their desktop stub implementations return neutral values and should not
be mistaken for hardware emulation.

`EmitTestKeyEvent` can be called manually in editor-only workflows to exercise a
Blueprint binding. No synthetic input is emitted automatically.
