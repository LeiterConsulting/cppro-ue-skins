# CPPRO Skin Loader

CPPRO Skin Loader is an installer-free desktop utility for sending compatible
`.pak` skins to slots 1–5 on a Finalmouse Centerpiece Pro.

One application codebase now targets:

- Windows 10/11 x86-64 through the proven `pywinusb` transport;
- Linux x86-64 through HIDAPI, including WSL 2 when USB is forwarded;
- macOS on Apple Silicon and Intel through HIDAPI.

The library interface provides:

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
example can therefore appear without rebuilding or redistributing the desktop
application. See the [skin library standard](../../examples/SKIN_STANDARD.md).

## Platform status

| Platform | Packaging | Transport | Validation |
| --- | --- | --- | --- |
| Windows x86-64 | Portable `.exe` | `pywinusb` | Physical upload confirmed |
| Linux x86-64 | Portable PyInstaller binary | HIDAPI/hidraw | WSL build, UI, protocol, and simulated transport tests |
| macOS arm64 | Ad-hoc-signed `.app` in `.dmg` | HIDAPI/IOKit | CI build; physical test pending |
| macOS x86-64 | Ad-hoc-signed `.app` in `.dmg` | HIDAPI/IOKit | CI build; physical test pending |

The Linux and macOS transports preserve the exact confirmed framing, upload
windowing, acknowledgement handling, completion check, and slot activation
sequence. Until a real upload is completed on each OS, they remain candidates
rather than device-confirmed releases.

## Download

Download the current cross-platform beta from
[v0.2.0-beta.1](https://github.com/LeiterConsulting/cppro-ue-skins/releases/tag/v0.2.0-beta.1):

- Windows: `CPPRO-Skin-Loader-Windows-x86_64.exe`
- Apple Silicon Mac: `CPPRO-Skin-Loader-macOS-arm64.dmg`
- Intel Mac: `CPPRO-Skin-Loader-macOS-x86_64.dmg`
- Linux x86-64: `CPPRO-Skin-Loader-Linux-x86_64`

On Linux, make the download executable before launching it:

```bash
chmod +x CPPRO-Skin-Loader-Linux-x86_64
./CPPRO-Skin-Loader-Linux-x86_64
```

Install the release's `70-cppro-skin-loader.rules` file before attempting a
real Linux upload. Verify all downloads against the included
`SHA256SUMS.txt`.

## Run from source

### Windows

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r `
  .\apps\windows-loader\requirements-windows.txt

# Safe evaluation: no device writes.
./.venv/Scripts/python.exe .\apps\windows-loader\entry.py --demo
```

### Linux or WSL

```bash
python3 -m venv ~/.venvs/cppro-loader
~/.venvs/cppro-loader/bin/python -m pip install \
  -r apps/windows-loader/requirements-unix.txt

# Safe evaluation: no device writes.
~/.venvs/cppro-loader/bin/python apps/windows-loader/entry.py --demo
```

Native Linux users should install the included udev rule before a real upload:

```bash
sudo install -m 0644 \
  apps/windows-loader/packaging/linux/70-cppro-skin-loader.rules \
  /etc/udev/rules.d/70-cppro-skin-loader.rules
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Reconnect the keyboard afterward. The rule grants the active desktop user
access to only the CPPRO HID interfaces.

WSL does not receive USB devices directly. Follow Microsoft's
[USB/IP instructions](https://learn.microsoft.com/windows/wsl/connect-usb) to
install `usbipd-win`, bind the CPPRO, and attach it to WSL. While attached, the
keyboard interface is unavailable to Windows.

### macOS

```bash
python3 -m venv .venv
./.venv/bin/python -m pip install \
  -r apps/windows-loader/requirements-unix.txt

# Safe evaluation: no device writes.
./.venv/bin/python apps/windows-loader/entry.py --demo
```

For the CI-built candidate, open the DMG, move the application to
`Applications`, and launch it. Because the candidate is ad-hoc signed rather
than Developer ID signed and notarized, macOS will require explicit user
approval before its first launch.

## Build standalone applications

Windows:

```powershell
./apps/windows-loader/build.ps1
```

Linux:

```bash
PYTHON=~/.venvs/cppro-loader/bin/python \
  bash apps/windows-loader/build-linux.sh
```

macOS:

```bash
PYTHON=.venv/bin/python bash apps/windows-loader/build-macos.sh
```

Build results are written under `artifacts/skin-loader/<platform>/`. The
`Build deployment apps` GitHub workflow creates downloadable Linux, Apple
Silicon macOS, and Intel macOS candidates on demand.

Every build stops before packaging if:

- the generated skin catalog is stale;
- loader or runtime tests fail;
- an example PAK, checksum, byte count, PAK version, or library manifest is
  invalid.

## macOS manual test checklist

Test `--demo` or the packaged application before a real transfer:

1. Confirm the app opens and the online library loads.
2. Confirm `CPPRO connected` appears with the keyboard attached directly.
3. Open a local known-good PAK and verify its size and checksum appear.
4. Use a nonessential slot and keep a known-good skin in another slot.
5. Send without activation first; wait for the success confirmation.
6. Activate the slot and verify the keyboard loads the skin.
7. Quit and reopen the app, then repeat detection once.

Record the Mac model, CPU architecture, macOS version, connection type, chosen
slot, transfer result, and whether activation succeeded.

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
