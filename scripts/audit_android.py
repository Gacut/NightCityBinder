"""Inspect AAB identity, target SDK and native ELF alignment; not full Play validation."""
import argparse
import hashlib
import json
import re
import struct
import zipfile
from pathlib import Path


def _read_varint(data, offset):
    value = 0
    for shift in range(0, 70, 7):
        byte = data[offset]
        offset += 1
        value |= (byte & 0x7f) << shift
        if not byte & 0x80:
            return value, offset
    raise ValueError('Invalid protobuf varint')


def _bundle_attribute(data, name):
    # AAB manifests use protobuf XML. XmlAttribute.name is field 2 and its
    # string value is field 3. Both fields are length-delimited here.
    encoded = name.encode('ascii')
    matches = list(re.finditer(b'\x12' + bytes([len(encoded)]) + encoded + b'\x1a', data))
    if len(matches) != 1:
        raise ValueError(f'Expected one {name} attribute in AAB manifest')
    length, offset = _read_varint(data, matches[0].end())
    return data[offset:offset + length].decode('utf-8')


def inspect(path, expected_abi=None, expected_package=None, min_target_sdk=None):
    rows = []
    with zipfile.ZipFile(path) as archive:
        manifest = archive.read('base/manifest/AndroidManifest.xml') if expected_package or min_target_sdk else None
        manifest_package = _bundle_attribute(manifest, 'package') if expected_package else None
        target_sdk = int(_bundle_attribute(manifest, 'targetSdkVersion')) if min_target_sdk else None
        for name in archive.namelist():
            if not name.endswith('.so'):
                continue
            data = archive.read(name)
            if data[:4] != b'\x7fELF':
                continue  # p4a libpybundle.so is a tar archive, not native code.
            endian = '<' if data[5] == 1 else '>'
            wide = data[4] == 2
            offset = struct.unpack_from(endian + ('Q' if wide else 'I'), data, 32 if wide else 28)[0]
            size, count = struct.unpack_from(endian + 'HH', data, 54 if wide else 42)
            segments = []
            for i in range(count):
                start = offset + i * size
                if struct.unpack_from(endian + 'I', data, start)[0] != 1:
                    continue
                if wide:
                    file_offset, address = struct.unpack_from(endian + 'QQ', data, start + 8)
                    alignment = struct.unpack_from(endian + 'Q', data, start + 48)[0]
                else:
                    file_offset, address = struct.unpack_from(endian + 'II', data, start + 4)
                    alignment = struct.unpack_from(endian + 'I', data, start + 28)[0]
                segments.append(alignment >= 16384 and (address - file_offset) % 16384 == 0)
            rows.append({'library': name, 'bits': 64 if wide else 32,
                         'elf_16kb': bool(segments) and all(segments)})
    unexpected_abis = sorted({name.split('/lib/', 1)[1].split('/', 1)[0]
                              for name in (r['library'] for r in rows)
                              if '/lib/' in name and expected_abi
                              and not name.startswith('base/lib/' + expected_abi + '/')})
    return {'artifact': Path(path).name, 'sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'native_libraries': rows,
            'elf_16kb': any(r['bits'] == 64 for r in rows) and all(r['elf_16kb'] for r in rows if r['bits'] == 64),
            'expected_abi': expected_abi,
            'unexpected_abis': unexpected_abis,
            'manifest_package': manifest_package,
            'expected_package': expected_package,
            'package_matches': expected_package is None or manifest_package == expected_package,
            'target_sdk': target_sdk,
            'min_target_sdk': min_target_sdk,
            'target_sdk_matches': min_target_sdk is None or target_sdk >= min_target_sdk,
            'limits': 'Preliminary checks only: also verify with bundletool, signature and a 16 KB device.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--expected-abi')
    parser.add_argument('--expected-package')
    parser.add_argument('--min-target-sdk', type=int)
    args = parser.parse_args()
    result = inspect(args.artifact, args.expected_abi, args.expected_package, args.min_target_sdk)
    output = json.dumps(result, indent=2)
    print(output)
    if args.report:
        args.report.write_text(output + '\n', encoding='utf-8')
    raise SystemExit(0 if result['elf_16kb'] and not result['unexpected_abis']
                     and result['package_matches'] and result['target_sdk_matches'] else 1)
