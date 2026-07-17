# Keyfield A2

Keyfield A2 is the first complete example in this repository. It demonstrates
the confirmed 1920×550 canvas, all 68 physical key regions, reliable
press/release input, bounded pooled effects, readable status areas, and a small
application state machine.

## Controls

| Key | Behavior |
| --- | --- |
| Enter | Start from Ready or resume from Paused |
| Escape | Pause while Live |
| Backspace | Return to Ready |
| Tab | Cycle cyan, magenta, and amber palettes |
| Any key while Live | Light the key and emit the bounded release/wave effects |

Release events remain active outside Live so state changes cannot leave a key
visually latched.

## Contents

- `manifest/` — reviewable designer configuration.
- `generated/keyfield-a2.svg` — desktop layout preview.
- `generated/keyfield-a2.lock.json` — hashes and resolved configuration.
- `release/cppro_keyfield_a2.pak` — the exact device-tested build.
- `../../project/Content/CPPRO/KeyfieldA2/` — editable UE4.27 Blueprint assets.

The PAK is 31,638,130 bytes. Its expected SHA-256 is recorded in
`release/SHA256SUMS.txt`.

The JSON manifest is currently a validated design contract and preview source;
it is not a general JSON-to-Blueprint compiler. Edit the included Blueprint
assets for runtime behavior, and keep the manifest synchronized with intentional
design changes.
