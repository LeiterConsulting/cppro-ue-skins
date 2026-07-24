# CPPRO Skin Loader for Windows

CPPRO Skin Loader is an installer-free Windows utility for sending compatible
`.pak` skins to slots 1–5 on a Finalmouse Centerpiece Pro.

The selected library interface provides:

- automatic CPPRO detection using VID `361D` and PID `0202`;
- the device-tested 1024-byte HID upload protocol;
- local Unreal PAK version-11 preflight;
- a scrollable online library generated from the repository examples;
- newest, A–Z, and GitHub Release download-count sorting;
- cached downloads with SHA-256 verification;
- local `.pak` selection;
- explicit destination-slot selection and optional activation;
- progress, completion, and actionable error states;
- `--demo` mode, which exercises the workflow without touching a keyboard.

The online catalog is refreshed when the application opens. A newly published
example can therefore appear without rebuilding or redistributing the Windows
application. See the [skin library standard](../../examples/SKIN_STANDARD.md).

## Download

Download `CPPRO-Skin-Loader.exe` and its checksum from the
[latest GitHub Release](https://github.com/LeiterConsulting/cppro-ue-skins/releases/latest).
The application is portable: save it anywhere and run it directly.

The initial community build is unsigned and may trigger a Windows SmartScreen
warning. Verify `SHA256SUMS.txt` before running it. Public binaries should be
Authenticode-signed when a suitable certificate is available.

## Run from source

From the repository root:

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r `
  .\apps\windows-loader\requirements-build.txt

# Safe evaluation: no device writes.
./.venv/Scripts/python.exe .\apps\windows-loader\entry.py --demo
```

Omit `--demo` only when a CPPRO is connected and you intend to write a slot.

## Build the standalone executable

```powershell
./apps/windows-loader/build.ps1
```

The one-file executable and `SHA256SUMS.txt` are written to
`artifacts/windows-loader/`. Build output is intentionally ignored by Git and
the executable is published as a GitHub Release asset.

The build stops before packaging if:

- the generated skin catalog is stale;
- loader or runtime tests fail;
- an example PAK, checksum, byte count, PAK version, or library manifest is
  invalid.

## Download counts

GitHub does not publish download counts for raw files stored in a repository.
Library PAKs are therefore also distributed as GitHub Release assets. The app
queries the public Releases API and totals assets with the matching filename.
Counts are informational and gracefully fall back to zero when offline.

## Safety boundary

The user must confirm immediately before a slot write. The application never
writes while browsing, downloading, checking a PAK, or detecting the keyboard.
Do not disconnect the CPPRO during transfer. Keep a known-good skin in another
slot because an incompatible custom skin can reset the selected slot.
