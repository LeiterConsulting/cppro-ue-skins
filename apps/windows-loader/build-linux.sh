#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="$(cd "$root/../.." && pwd)"
python="${PYTHON:-python3}"
out_dir="${OUT_DIR:-$repo/artifacts/skin-loader/linux-x86_64}"
work_dir="$root/build/linux"
spec_dir="$root/spec/linux"

"$python" "$root/make_icon.py"
PYTHONPATH="$root" "$python" -m unittest discover -s "$root/tests" -v
"$python" "$repo/tools/build-skin-catalog.py" --check
"$python" "$root/verify_catalog.py"

mkdir -p "$out_dir" "$work_dir" "$spec_dir"

"$python" -m PyInstaller \
  --noconfirm \
  --clean \
  --onefile \
  --windowed \
  --name "CPPRO-Skin-Loader" \
  --icon "$root/assets/cppro-loader.png" \
  --paths "$root" \
  --hidden-import hid \
  --add-data "$repo/catalog/skins.json:catalog" \
  --add-data "$root/assets:assets" \
  --distpath "$out_dir" \
  --workpath "$work_dir" \
  --specpath "$spec_dir" \
  "$root/entry.py"

chmod +x "$out_dir/CPPRO-Skin-Loader"
(cd "$out_dir" && sha256sum "CPPRO-Skin-Loader" > "SHA256SUMS.txt")
ls -lh "$out_dir/CPPRO-Skin-Loader" "$out_dir/SHA256SUMS.txt"
