#!/usr/bin/env bash
# Run in Ubuntu after build_android.sh has produced the unsigned Play bundle.
# jarsigner prompts for the keystore password; no password is passed on the command line.
set -euo pipefail

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
version="$(awk -F ' *= *' '/^version =/{print $2; exit}' "$source_dir/buildozer.spec")"
unsigned="$source_dir/dist/NightCityBinder-$version-unsigned.aab"
signed="$source_dir/dist/NightCityBinder-$version-play.aab"
keystore="${NCB_UPLOAD_KEYSTORE:-$HOME/.android-keys/nightcitybinder-upload.jks}"
alias_name="${NCB_UPLOAD_ALIAS:-upload}"
audit="$source_dir/dist/play-native-audit.json"

if [[ ! -s "$unsigned" ]]; then
  printf 'Unsigned bundle not found: %s\nBuild it with NCB_BUILD_MODE=play first.\n' "$unsigned" >&2
  exit 1
fi
if ! python3 - "$unsigned" "$audit" <<'PY'
import hashlib
import json
import sys
from pathlib import Path

bundle, report = map(Path, sys.argv[1:])
try:
    data = json.loads(report.read_text(encoding='utf-8'))
    valid = (
        data.get('artifact') == bundle.name
        and data.get('sha256') == hashlib.sha256(bundle.read_bytes()).hexdigest()
        and data.get('elf_16kb') is True
        and data.get('expected_abi') == 'arm64-v8a'
        and data.get('unexpected_abis') == []
        and data.get('manifest_package') == 'com.nightcitybinder'
        and data.get('expected_package') == 'com.nightcitybinder'
        and data.get('package_matches') is True
        and data.get('target_sdk', 0) >= 36
        and data.get('min_target_sdk') == 36
        and data.get('target_sdk_matches') is True
    )
except (OSError, ValueError):
    valid = False
if not valid:
    print('The AAB does not match a passing package/API 36/ARM64/16 KB audit. Rebuild it before signing.', file=sys.stderr)
    sys.exit(1)
PY
then
  exit 1
fi
if [[ ! -f "$keystore" ]]; then
  printf 'Upload keystore not found: %s\n' "$keystore" >&2
  printf 'Create or select a private upload key before signing; see docs/play/README.md.\n' >&2
  exit 1
fi
if [[ -e "$signed" ]]; then
  printf 'Signed bundle already exists; refusing to overwrite: %s\n' "$signed" >&2
  exit 1
fi

jarsigner -keystore "$keystore" -signedjar "$signed" "$unsigned" "$alias_name"
verification="$(jarsigner -J-Duser.language=en -J-Duser.country=US -verify -verbose -certs "$signed")"
printf '%s\n' "$verification"
if [[ "$verification" != *"jar verified."* ]]; then
  printf 'Bundle signature could not be verified. Do not upload it.\n' >&2
  exit 1
fi
sha256sum "$signed" > "$signed.sha256"
printf 'Signed Play bundle: %s\n' "$signed"
