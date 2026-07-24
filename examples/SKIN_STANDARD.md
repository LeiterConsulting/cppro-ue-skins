# Skin library standard

Every public example is both a documented source project and an installable
library item. The standard keeps those two roles synchronized so a new example
appears in CPPRO Skin Loader without editing application code.

## Required example layout

```text
examples/<skin-id>/
├── README.md
├── library.json
├── release/
│   ├── <unique-name>.pak
│   └── SHA256SUMS.txt
└── ...source, artwork, manifests, and tools needed to reproduce it
```

`<skin-id>` must be lowercase kebab-case and must equal `id` in
`library.json`. Each example has exactly one `.pak` selected by `pak`.

## `library.json`

```json
{
  "schema": "cppro-skin-library-entry",
  "version": 1,
  "id": "example-skin",
  "name": "Example Skin",
  "subtitle": "Short library-card summary",
  "description": "One concise explanation of its behavior and value.",
  "tags": ["Reactive", "Animated"],
  "accent": "#18A7C9",
  "published_at": "2026-07-24T12:00:00-04:00",
  "pak": "release/cppro_example_skin.pak",
  "release": {
    "tag": "v0.2.0",
    "asset": "cppro_example_skin.pak"
  }
}
```

The formal contract is
[`schemas/library-entry.schema.json`](../schemas/library-entry.schema.json).

- `published_at` is the first public availability date, not the last edit
  time. Keep it stable when documentation is corrected.
- `release.asset` must equal the PAK filename and must be unique across the
  repository.
- `release.tag` identifies the GitHub Release that will host that exact PAK.
- The PAK filename should include the skin identity. When an incompatible skin
  revision needs separate download accounting, give the asset a new filename.

## Add or update an example

1. Add the documented example folder, `library.json`, release PAK, and
   `SHA256SUMS.txt`.
2. Build the catalog:

   ```powershell
   python tools/build-skin-catalog.py
   ```

3. Run the same checks used in CI:

   ```powershell
   python tools/build-skin-catalog.py --check
   python apps/windows-loader/verify_catalog.py
   ```

4. Commit the example and generated `catalog/skins.json` together.
5. Attach `release.asset` to the GitHub Release named by `release.tag`.

The generator refuses duplicate IDs, duplicate PAK paths, duplicate release
asset names, missing documentation, invalid timestamps/colors, checksum
mismatches, non-version-11 PAKs, or catalog drift.

## Downloads

Raw repository files do not expose per-file download counts. The Windows
loader therefore queries GitHub's public Releases API and totals the download
count of matching release assets. If GitHub is unavailable, the library still
works and retains the last catalog value, normally zero.

This makes **Most downloaded** a meaningful sort while keeping **Newest** and
**A–Z** deterministic and available offline.
