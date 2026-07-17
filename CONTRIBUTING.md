# Contributing

Contributions should stay inside the public authoring boundary:

- original skin source, manifests, schemas, examples, and documentation;
- generic build, validation, and packaging improvements;
- sanitized hardware observations that do not expose unrelated USB traffic or
  personal information.

Do not submit vendor binaries, firmware, official or extracted skin assets,
XPanel packages, packet captures, credentials, local build products, or content
whose redistribution rights are unclear.

Before opening a pull request:

1. Run `python tools/cppro_skin_kit.py validate <manifest>`.
2. Run `python -m unittest discover -s reference/runtime -v`.
3. If the Unreal project changed, open it in UE4.27 and cook Android ASTC.
4. If a PAK changed, run `tools/verify-pak.ps1`.
5. Record the exact PAK SHA-256 and describe any on-device result separately
   from offline validation.

Please keep generated PAKs under GitHub's normal file-size limit. Never replace
an accepted example PAK without updating its checksum and test notes.
