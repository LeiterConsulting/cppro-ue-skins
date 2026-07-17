# PAK format and build contract

A compatible build uses:

- Unreal Engine 4.27;
- Android ASTC cooking;
- PAK version 11;
- mount point `../../../`;
- top-level staged paths `Engine/` and `spark/`;
- canonical map `spark/Content/map/M_EntryPoint.umap`;
- project/module name `spark`.

The repository's build script establishes that layout from the cooked project.
Do not pack the source project directory directly. Editor folders such as
`Binaries`, `Intermediate`, `Saved`, and `DerivedDataCache` do not belong in the
PAK.

Run:

```powershell
./tools/build-pak.ps1 -EngineRoot 'D:\Epic Games\UE_4.27'
./tools/verify-pak.ps1 -Pak .\artifacts\cppro_skin.pak `
  -EngineRoot 'D:\Epic Games\UE_4.27'
```

`verify-pak.ps1` checks UnrealPak integrity, the canonical map count, expected
mount path, and SHA-256. It does not prove device compatibility; only a
controlled physical load can do that.
