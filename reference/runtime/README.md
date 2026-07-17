# Headless reference runtime

This dependency-free model lets authors test input edges, semantic profiles, and
application states without Unreal or hardware. It is not shipped to the
keyboard.

Run from the repository root:

```powershell
python -m unittest discover -s reference/runtime -v
```

The intended Blueprint layering is:

```text
SkinApi event -> input adapter -> native key index -> semantic profile
              -> state/mode -> bounded view effects
```
