#!/usr/bin/env bash
# Run under Ubuntu 24.04 / WSL2. First build requires internet and several GB of disk.
# The agent can edit this file on Windows; launch it from Ubuntu when WSL access
# from the agent's restricted session is denied.
set -euo pipefail
build_mode="${NCB_BUILD_MODE:-debug}"
case "$build_mode" in debug|play) ;; *) printf 'Use debug or play mode.\n' >&2; exit 1 ;; esac
# Build unsigned, sign interactively afterwards: never expose passwords in logs.
if [[ "$build_mode" == play ]]; then
  unset P4A_RELEASE_KEYSTORE P4A_RELEASE_KEYSTORE_PASSWD P4A_RELEASE_KEYALIAS P4A_RELEASE_KEYALIAS_PASSWD
fi

source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
version="$(awk -F ' *= *' '/^version =/{print $2; exit}' "$source_dir/buildozer.spec")"
build_dir="${NCB_BUILD_DIR:-/var/tmp/nightcitybinder-build-${UID}}"
case "$build_dir" in
  /mnt/*) printf 'Build in the Linux filesystem, not under /mnt.\n' >&2; exit 1 ;;
esac
if [[ "$(uname -s)" != Linux ]]; then
  printf 'Ubuntu / WSL2 is required.\n' >&2
  exit 1
fi

mkdir -p "$source_dir/dist"
windows_log="$source_dir/dist/build-$(date +%Y%m%d-%H%M%S).log"
exec > >(tee -a "$windows_log") 2>&1
printf 'Build log: %s\n' "$windows_log"

sudo apt-get update
sudo apt-get install -y git zip unzip openjdk-17-jdk python3-pip python3-venv \
  build-essential autoconf automake libtool pkg-config zlib1g-dev libncurses-dev \
  cmake libffi-dev libssl-dev rsync

mkdir -p "$build_dir/project" "$build_dir/logs"
# No deletion; keep the SDK, NDK and previous build cache for subsequent runs.
rsync -a --exclude=.git --exclude=.local --exclude=.venv --exclude=.buildozer \
  --exclude=bin --exclude=dist --exclude=__pycache__ --exclude=.pytest_cache \
  --exclude=.ruff_cache "$source_dir/" "$build_dir/project/"
if [[ ! -x "$build_dir/venv/bin/python" ]]; then
  python3 -m venv "$build_dir/venv"
fi
"$build_dir/venv/bin/python" -m pip install 'buildozer==1.6.0' 'Cython==0.29.37' setuptools
source "$build_dir/venv/bin/activate"
cd "$build_dir/project"
export PIP_CONSTRAINT="$build_dir/project/android/pip-constraints.txt"
printf 'Pip dependency constraint: %s\n' "$PIP_CONSTRAINT"

# p4a re-runs `hostpython -m venv venv` on an existing temporary environment.
# Its bundled pip can overlap a previously upgraded pip, leaving mixed files.
# Archive ONLY this generated environment; p4a recreates it. Keep native builds,
# the outer Buildozer environment, SDK, NDK, and downloaded packages untouched.
temporary_parent="$build_dir/project/.buildozer/android/platform/build-arm64-v8a/build"
temporary_venv="$temporary_parent/venv"
if [[ -e "$temporary_venv" ]]; then
  canonical_build="$(realpath -- "$build_dir")"
  canonical_venv="$(realpath -- "$temporary_venv")"
  if [[ "$canonical_venv" != "$canonical_build/project/.buildozer/android/platform/build-arm64-v8a/build/venv" ]]; then
    printf 'Unexpected temporary venv path; refusing to move: %s\n' "$canonical_venv" >&2
    exit 1
  fi
  recovery_dir="$(mktemp -d "$temporary_parent/pip-recovery-XXXXXXXX")"
  mv -- "$temporary_venv" "$recovery_dir/venv"
  printf 'Archived temporary pip environment: %s/venv\n' "$recovery_dir"
fi

log_file="$build_dir/logs/build-$(date +%Y%m%d-%H%M%S).log"
touch "$build_dir/build-started"
if [[ "$build_mode" == play ]]; then
  buildozer --profile play -v android release 2>&1 | tee "$log_file"
  gradle_project="$build_dir/project/.buildozer/android/platform/build-arm64-v8a/dists/nightcitybinder"
  gradle_file="$gradle_project/build.gradle"
  if [[ ! -f "$gradle_file" || ! -x "$gradle_project/gradlew" ]]; then
    printf 'Generated Gradle project is missing: %s\n' "$gradle_project" >&2
    exit 1
  fi
  # The cached p4a distribution can retain API 35 in its generated Gradle
  # project even when Buildozer requests 36. Transitive AARs also add other
  # ABIs. Apply both settings to the final Gradle bundle build.
  python - "$gradle_file" <<'PY'
from pathlib import Path
import re
import sys

path = Path(sys.argv[1])
source = path.read_text(encoding='utf-8')
needle = 'defaultConfig {'
if source.count(needle) != 1:
    raise SystemExit(f'Expected one defaultConfig block in {path}')
if "abiFilters 'arm64-v8a'" not in source:
    source = source.replace(needle, needle + "\n        ndk { abiFilters 'arm64-v8a' }", 1)
for setting in ('compileSdkVersion', 'targetSdkVersion'):
    pattern = rf'(?m)^([ \t]*{setting}[ \t]+)\d+([ \t]*)$'
    source, count = re.subn(pattern, r'\g<1>36\2', source)
    if count != 1:
        raise SystemExit(f'Expected one {setting} in {path}; found {count}')
path.write_text(source, encoding='utf-8')
print(f'Gradle ARM64 ABI filter and API 36 verified in {path}')
PY
  (cd "$gradle_project" && ./gradlew clean bundleRelease --console=plain) 2>&1 | tee -a "$log_file"
  bundle="$gradle_project/build/outputs/bundle/release/nightcitybinder-release.aab"
  if [[ ! -s "$bundle" ]]; then
    printf 'Gradle did not produce an AAB: %s\n' "$bundle" >&2
    exit 1
  fi
  destination="$source_dir/dist/NightCityBinder-$version-unsigned.aab"
  cp -- "$bundle" "$destination"
  sha256sum "$destination" > "$destination.sha256"
  python "$source_dir/scripts/audit_android.py" "$destination" --expected-abi arm64-v8a --expected-package com.nightcitybinder --min-target-sdk 36 --report "$source_dir/dist/play-native-audit.json"
  printf 'Unsigned candidate: %s. Read docs/play/README.md before signing.\n' "$destination"
  exit 0
fi
if ! buildozer -v android debug 2>&1 | tee "$log_file"; then
  printf '\nBuildozer failed. Collecting the Gradle packaging stacktrace...\n'
  if NCB_BUILD_DIR="$build_dir" bash "$source_dir/scripts/diagnose_android_package.sh"; then
    exit 0
  fi
  exit 1
fi

# Copy only an APK produced by this successful build.
mapfile -t apks < <(find "$build_dir/project/bin" -maxdepth 1 -type f -name '*debug.apk' -newer "$build_dir/build-started")
if [[ ${#apks[@]} -ne 1 ]]; then
  printf 'Expected one debug APK, found %s. Inspect %s\n' "${#apks[@]}" "$build_dir/project/bin" >&2
  exit 1
fi
mkdir -p "$source_dir/dist"
cp -- "${apks[0]}" "$source_dir/dist/NightCityBinder-$version.apk"
cd "$source_dir/dist"
sha256sum "NightCityBinder-$version.apk" > "NightCityBinder-$version.apk.sha256"
printf '\nAPK saved to %s/dist/NightCityBinder-%s.apk\n' "$source_dir" "$version"
