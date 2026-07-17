# Safety and compatibility

Custom interactive skins are unsupported by the vendor. Treat every new PAK as
an experiment.

## Before writing a slot

1. Keep at least one known-good skin in another slot.
2. Use a nonessential slot; examples use slot 5.
3. Validate and inspect the PAK offline.
4. Record its SHA-256.
5. Close other tools that may hold the CPPRO HID interface.
6. Keep the keyboard powered and connected throughout the upload.

The uploader is dry-run by default. Hardware writes require `--send`. The
`--activate` option switches away and back only after a successful transfer.

## If a skin crashes

The keyboard may reset and clear the affected slot. Select another working slot
and rebuild the experimental PAK. Do not repeatedly reload a crashing skin
without first reducing it to known-safe UMG/input behavior.

## Compatibility statement

The included A2 artifact was built with UE4.27, accepted by the tested
Centerpiece Pro, returned the device success status `00 00`, remounted, and
remained stable during typing. That does not guarantee compatibility across all
firmware revisions or future vendor updates.

## Technologies not established by this kit

Networking, host data exchange, audio, persistence, Android APIs, native runtime
code, and unrestricted Niagara use are not part of the stable example contract.
Test such capabilities independently before combining them with a real skin.
