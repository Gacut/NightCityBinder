#!/usr/bin/env bash
# Re-run only Gradle's failing APK packaging step and save the real exception.
set -uo pipefail

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${NCB_BUILD_DIR:-/var/tmp/nightcitybinder-build-${UID}}"
gradle_dir="$build_dir/project/.buildozer/android/platform/build-arm64-v8a/dists/nightcitybinder"
if [[ ! -x "$gradle_dir/gradlew" ]]; then
  printf 'Gradle project not found: %s\nRun build_android.sh first.\n' "$gradle_dir" >&2
  exit 1
fi

mkdir -p "$source_dir/dist"
report="$source_dir/dist/gradle-package-diagnostic-$(date +%Y%m%d-%H%M%S).log"
{
  printf 'Gradle project: %s\n' "$gradle_dir"
  printf 'Diagnostic log: %s\n' "$report"
  printf '\nLinux filesystem space and inodes:\n'
  df -h "$build_dir" "$HOME"
  df -i "$build_dir" "$HOME"
  printf '\nMemory:\n'
  free -h
  printf '\nGradle packageDebug with stacktrace:\n'
  cd "$gradle_dir"
  ./gradlew :packageDebug --stacktrace --info --console=plain
} 2>&1 | tee "$report"
result=${PIPESTATUS[0]}
printf '\nDiagnostic saved to: %s\n' "$report"
if [[ "$result" -ne 0 ]]; then
  exit "$result"
fi

# Gradle sometimes succeeds on the second package attempt even though p4a has
# already stopped. Recover only a new, readable APK with the expected identity.
set -e
apk="$gradle_dir/build/outputs/apk/debug/nightcitybinder-debug.apk"
if [[ ! -s "$apk" || ! "$apk" -nt "$build_dir/build-started" ]]; then
  printf 'No fresh APK to recover at %s\n' "$apk" >&2
  exit 1
fi
unzip -tqq "$apk"
sdk_dir="$HOME/.buildozer/android/platform/android-sdk/build-tools"
aapt="$(find "$sdk_dir" -maxdepth 2 -type f -name aapt -print | sort -V | tail -n 1)"
if [[ ! -x "$aapt" ]]; then
  printf 'Android aapt not found under %s; APK was not copied.\n' "$sdk_dir" >&2
  exit 1
fi
badging="$("$aapt" dump badging "$apk")"
version="$(awk -F ' *= *' '/^version =/{print $2; exit}' "$source_dir/buildozer.spec")"
if [[ "$badging" != *"name='com.nightcitybinder'"* ||
      "$badging" != *"versionName='$version'"* ]]; then
  printf 'APK package name or version differs from buildozer.spec; refusing to copy.\n' >&2
  printf '%s\n' "$badging" | head -n 1 >&2
  exit 1
fi
destination="$source_dir/dist/NightCityBinder-$version.apk"
cp -- "$apk" "$destination"
sha256sum "$destination" > "$destination.sha256"
printf 'Verified APK recovered to: %s\n' "$destination"
