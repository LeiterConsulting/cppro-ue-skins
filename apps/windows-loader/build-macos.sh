#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$root/../.." && pwd)"
python="${PYTHON:-python3}"
arch="$(uname -m)"
out_dir="${OUT_DIR:-$repo/artifacts/skin-loader/macos-$arch}"
work_dir="$root/build/macos-$arch"
spec_dir="$root/spec/macos-$arch"
dist_dir="$out_dir/dist"
app="$dist_dir/CPPRO-Skin-Loader.app"
dmg="$out_dir/CPPRO-Skin-Loader-macOS-$arch.dmg"

"$python" "$root/make_icon.py"
PYTHONPATH="$root" "$python" -m unittest discover -s "$root/tests" -v
"$python" "$repo/tools/build-skin-catalog.py" --check
"$python" "$root/verify_catalog.py"

mkdir -p "$out_dir" "$work_dir" "$spec_dir" "$dist_dir"

"$python" -m PyInstaller \
  --noconfirm \
  --clean \
  --windowed \
  --name "CPPRO-Skin-Loader" \
  --osx-bundle-identifier "com.leiterconsulting.cppro-skin-loader" \
  --icon "$root/assets/cppro-loader.icns" \
  --paths "$root" \
  --hidden-import hid \
  --add-data "$repo/catalog/skins.json:catalog" \
  --add-data "$root/assets:assets" \
  --distpath "$dist_dir" \
  --workpath "$work_dir" \
  --specpath "$spec_dir" \
  "$root/entry.py"

# Ad-hoc signing makes the bundle internally consistent. Public notarization
# requires an Apple Developer identity and is intentionally a later release step.
codesign --force --deep --sign - "$app"
codesign --verify --deep --strict "$app"

rm -f "$dmg"
hdiutil create \
  -volname "CPPRO Skin Loader" \
  -srcfolder "$app" \
  -ov \
  -format UDZO \
  "$dmg"

shasum -a 256 "$dmg" > "$out_dir/SHA256SUMS.txt"
ls -lh "$dmg" "$out_dir/SHA256SUMS.txt"
