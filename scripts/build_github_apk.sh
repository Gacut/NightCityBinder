#!/usr/bin/env bash
# Build and sign an installable APK for the GitHub release in Ubuntu/WSL.
# The upload keystore stays on the user's machine; apksigner prompts for its password.
set -euo pipefail

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
version="$(awk -F ' *= *' '/^version =/{print $2; exit}' "$source_dir/buildozer.spec")"
version_code="$(awk '/^\[app@play\]/{inside=1; next} /^\[/{inside=0} inside && /^android.numeric_version =/{print $3; exit}' "$source_dir/buildozer.spec")"
build_dir="${NCB_BUILD_DIR:-/var/tmp/nightcitybinder-build-${UID}}"
gradle_project="$build_dir/project/.buildozer/android/platform/build-arm64-v8a/dists/nightcitybinder"
keystore="${NCB_UPLOAD_KEYSTORE:-$HOME/.android-keys/nightcitybinder-upload.jks}"
alias_name="${NCB_UPLOAD_ALIAS:-upload}"
destination="$source_dir/dist/NightCityBinder-$version-github.apk"

if [[ "$(uname -s)" != Linux || "$build_dir" == /mnt/* ]]; then
  printf 'Run this script in Ubuntu/WSL, with the build cache in the Linux filesystem.\n' >&2
  exit 1
fi
if [[ ! -f "$keystore" ]]; then
  printf 'Upload keystore not found: %s\n' "$keystore" >&2
  exit 1
fi
if [[ -e "$destination" ]]; then
  printf 'Refusing to overwrite an existing release APK: %s\n' "$destination" >&2
  exit 1
fi

# Recreate the release Gradle project from the current source and apply its API 36
# and ARM64 settings using the same path as the Play bundle.
NCB_BUILD_MODE=play bash "$source_dir/scripts/build_android.sh"
if [[ ! -x "$gradle_project/gradlew" ]]; then
  printf 'Gradle project not found: %s\n' "$gradle_project" >&2
  exit 1
fi
(cd "$gradle_project" && ./gradlew assembleRelease --console=plain)
mapfile -t unsigned_apks < <(find "$gradle_project/build/outputs/apk/release" -maxdepth 1 -type f -name '*unsigned.apk')
if [[ ${#unsigned_apks[@]} -ne 1 ]]; then
  printf 'Expected one unsigned release APK, found %s.\n' "${#unsigned_apks[@]}" >&2
  exit 1
fi

sdk="${ANDROIDSDK:-$HOME/.buildozer/android/platform/android-sdk}"
build_tools="$(find "$sdk/build-tools" -mindepth 1 -maxdepth 1 -type d | sort -V | tail -n 1)"
if [[ ! -x "$build_tools/zipalign" || ! -x "$build_tools/apksigner" || ! -x "$build_tools/aapt" ]]; then
  printf 'Android build-tools not found under %s\n' "$sdk/build-tools" >&2
  exit 1
fi

mkdir -p "$source_dir/dist"
aligned="$(mktemp "$source_dir/dist/.nightcitybinder-aligned-XXXXXX.apk")"
trap 'rm -f -- "$aligned"' EXIT
"$build_tools/zipalign" -P 16 -f 4 "${unsigned_apks[0]}" "$aligned"
"$build_tools/apksigner" sign --ks "$keystore" --ks-key-alias "$alias_name" --out "$destination" "$aligned"
"$build_tools/apksigner" verify --verbose --print-certs "$destination"
"$build_tools/zipalign" -c -P 16 4 "$destination"
badging="$("$build_tools/aapt" dump badging "$destination")"
printf '%s\n' "$badging" | grep -E '^package:|^sdkVersion:|^targetSdkVersion:'
if [[ "$badging" != *"name='com.nightcitybinder'"* || "$badging" != *"versionName='$version'"* || "$badging" != *"versionCode='$version_code'"* || "$badging" != *"targetSdkVersion:'36'"* ]]; then
  printf 'APK identity or API level did not match the release.\n' >&2
  rm -f -- "$destination"
  exit 1
fi
sha256sum "$destination" > "$destination.sha256"
printf 'Signed GitHub APK: %s\n' "$destination"
