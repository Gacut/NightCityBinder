"""Copy exact bundled Python notices from a p4a APK/AAB without extracting paths."""
import argparse
import io
import tarfile
import zipfile
from pathlib import Path


def collect(artifact, output):
    notices = []
    with zipfile.ZipFile(artifact) as archive:
        name = next(n for n in archive.namelist() if n.endswith('/libpybundle.so'))
        with tarfile.open(fileobj=io.BytesIO(archive.read(name)), mode='r:*') as bundle:
            for member in bundle:
                basename = Path(member.name).name.upper()
                if member.isfile() and basename.startswith(('LICENSE', 'COPYING', 'NOTICE')):
                    text = bundle.extractfile(member).read().decode('utf-8', errors='replace')
                    notices.append(f'===== {member.name} =====\n{text}\n')
    output.write_text('Python notices extracted from ' + Path(artifact).name + '\n'
                      'Not a complete inventory of native/Java dependencies.\n\n'
                      + '\n'.join(notices), encoding='utf-8')
    print(f'{len(notices)} notices -> {output}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('artifact', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    collect(args.artifact, args.output)
