#!/usr/bin/env python3
"""Assemble Xargon Wars from the preserved source disk, recording every dependency."""

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import zipfile
import zlib
from pathlib import Path

from d64_image import D64Image
from source_converter import convert, flatten

ROOT = Path(__file__).resolve().parents[1]
INPUTS = ROOT / 'Original Source Recovered'
IMAGE = INPUTS / '2026/XargonWars-C16-d64copy.d64'
EXTRACTED = INPUTS / '2026/XargonWars-C16'
OLDER = INPUTS / '1992/DISK7A'
OLDER_ZIP = INPUTS / '1992/DISK7A - Xargon Wars C16.ZIP'
REFERENCE = ROOT / 'Original Artifacts/xargon_wars.prg'

ROOT_MODULE = 'ULTRA'
LOAD_ADDRESS = 0x1010
ENTRY_ADDRESS = 0x1C80
END_ADDRESS = 0x4000
# Separately loaded disk files that the source names but does not assemble.
# TUNE equates TUNDAT=$1C00; ULTRA says "JUST LOAD ON 'FRAK!' ... IT HAS ALL THE GRAPHICS".
DISK_ASSETS = [('MUSIC/CODE', 0x1C00, 'TUNDAT tune table (TUNE: TUNDAT=$1C00)'),
               ('FRAK!', 0x3C00, 'character set named by ULTRA')]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def tool(name):
    found = shutil.which(name)
    if found:
        return found
    for directory in ('/opt/homebrew/bin', '/usr/local/bin'):
        candidate = Path(directory) / name
        if candidate.is_file():
            return str(candidate)
    raise FileNotFoundError(f'{name} not found; install the cc65/VICE tools described in README.md')


def rel(path):
    return path.relative_to(ROOT).as_posix()


def cross_check_1992(disk_files):
    """Compare the 1992 PC export (lower case, CRLF) and its ZIP with the disk."""
    index = (OLDER / 'INDEX').read_bytes().decode('ascii')
    rows = re.findall(r'^\d+\s+"([^"]+)"\s+(SEQ|PRG)\s+(\S+)\s+(\S+)', index, re.MULTILINE)
    # PKZIP 1.0 implode/shrink cannot be decompressed by zipfile; the central
    # directory's CRC-32 and size still identify every member exactly enough.
    with zipfile.ZipFile(OLDER_ZIP) as archive:
        zipped = {Path(info.filename).name: (info.CRC, info.file_size)
                  for info in archive.infolist() if not info.is_dir()}
    folder = {p.name: p.read_bytes() for p in OLDER.iterdir()
              if p.is_file() and p.name != '.DS_Store'}
    unzipped = {name: (zlib.crc32(data), len(data)) for name, data in folder.items()}
    report = {'index_entries': len(rows), 'zip_matches_folder': zipped == unzipped,
              'zip_comparison': 'central-directory CRC-32 and size per member; .DS_Store ignored',
              'zip_sha256': digest(OLDER_ZIP.read_bytes()), 'files': []}
    for name, kind, stem, ext in rows:
        old = folder[f'{stem}.{ext}']
        new = disk_files[name].data
        if kind == 'SEQ':
            status = ('same text (upper case, CR line ends)'
                      if old.replace(b'\r\n', b'\r').upper() == new else 'different')
        elif ext == 'BIN':
            status = 'identical' if old == new else 'different'
        else:
            status = 'detokenized BASIC listing; not byte comparable'
        report['files'].append({'name': name, 'export': f'{stem}.{ext}',
                                'sha256': digest(old), 'status': status})
    differing = [f['name'] for f in report['files'] if f['status'] == 'different']
    if differing or len(rows) != len(disk_files) or not report['zip_matches_folder']:
        raise ValueError(f'1992 export does not match the disk: {differing}')
    return report


def prepare_sources(build):
    """Read the D64 directly and require agreement with the preserved 2026 extraction."""
    disk = D64Image(IMAGE).files()
    raw = build / 'disk'
    raw.mkdir(parents=True, exist_ok=True)
    extraction = json.loads((EXTRACTED / 'manifest.json').read_text())
    extracted = {bytes.fromhex(f['petscii_name_hex']).rstrip(b'\xa0').decode('ascii'): f
                 for f in extraction['files']}
    if extraction['source_sha256'] != digest(IMAGE.read_bytes()):
        raise ValueError('Preserved extraction was not made from this disk image')
    sources, files, by_name = {}, [], {}
    for number, file in enumerate(disk, 1):
        record = extracted.get(file.name)
        if record is None or file.data != (EXTRACTED / record['output']).read_bytes():
            raise ValueError(f'Disk and preserved 2026 extraction differ: {file.name}')
        if digest(file.data) != record['sha256']:
            raise ValueError(f'Extraction hash mismatch: {file.name}')
        (raw / record['output']).write_bytes(file.data)
        by_name[file.name] = file
        files.append({'name': file.name, 'kind': file.kind, 'directory_index': number,
                      'sha256': digest(file.data), 'bytes': len(file.data),
                      'blocks': file.blocks, 'closed': file.closed,
                      'extracted_copy': rel(EXTRACTED / record['output']),
                      'load_address': (f'${file.data[0] | file.data[1] << 8:04X}'
                                       if file.kind == 'PRG' else None)})
        if file.kind == 'SEQ':
            sources[file.name] = file.data.decode('ascii').split('\r')
    if len(disk) != len(extracted):
        raise ValueError('Disk and extraction contain different file counts')
    manifest = {'image': rel(IMAGE), 'image_sha256': digest(IMAGE.read_bytes()),
                'disk_files': len(disk), 'source_priority': '2026 D64 only; no fallback required',
                'files': files, 'older_export_cross_check': cross_check_1992(by_name)}
    (build / 'recovery-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return sources, by_name, manifest


def mos_hex(lines):
    """Decode MOS Technology hex records, validating checksums and terminator."""
    memory, records, terminal = {}, 0, False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if terminal:
            raise ValueError('Data after MOS hex terminator')
        if not line.startswith(';'):
            raise ValueError(f'Invalid MOS hex record: {line}')
        raw = bytes.fromhex(line[1:])
        if len(raw) < 5:
            raise ValueError('MOS hex record is too short')
        count = raw[0]
        if len(raw) != count + 5 or sum(raw[:-2]) != int.from_bytes(raw[-2:], 'big'):
            raise ValueError('MOS hex length/checksum mismatch')
        address = int.from_bytes(raw[1:3], 'big')
        if not count:
            if address != records:
                raise ValueError('MOS hex record count mismatch')
            terminal = True
            continue
        records += 1
        for offset, byte in enumerate(raw[3:-2]):
            if address + offset in memory:
                raise ValueError('Overlapping MOS hex records')
            memory[address + offset] = byte
    if not terminal:
        raise ValueError('Missing MOS hex terminator')
    return memory


def assemble(build, sources, name, stem, config):
    assembly = build / (stem + '.s')
    lines = flatten(sources, name)
    assembly.write_text(convert(lines))
    linker = build / (stem + '.cfg')
    linker.write_text(config.read_text().replace('%B', build.as_posix()))
    obj = build / (stem + '.o')
    subprocess.run([tool('ca65'), '-g', '-l', str(build / (stem + '.lst')),
                    '-o', str(obj), str(assembly)], check=True)
    subprocess.run([tool('ld65'), '-C', str(linker), '-o', str(build / (stem + '.bin')),
                    '-m', str(build / (stem + '.map')),
                    '-Ln', str(build / (stem + '.labels')), '--dbgfile', str(build / (stem + '.dbg')),
                    str(obj)], check=True)
    return list(dict.fromkeys(module for module, _, _ in lines))


def build_game(build):
    build = build.resolve()
    build.mkdir(parents=True, exist_ok=True)
    sources, disk, manifest = prepare_sources(build)
    used = assemble(build, sources, ROOT_MODULE, 'xargon', ROOT / 'config/c16.cfg')
    sheets = (build / 'sheets.bin').read_bytes()
    code = (build / 'code.bin').read_bytes()
    memory = bytearray(END_ADDRESS - LOAD_ADDRESS)

    def place(address, data):
        memory[address - LOAD_ADDRESS:address - LOAD_ADDRESS + len(data)] = data

    place(0x1010, sheets)
    place(ENTRY_ADDRESS, code)
    assets = []
    for name, address, purpose in DISK_ASSETS:
        data = disk[name].data
        if data[0] | data[1] << 8 != address:
            raise ValueError(f'{name} does not load at ${address:04X}')
        place(address, data[2:])
        assets.append({'name': name, 'source': rel(IMAGE), 'address': f'${address:04X}',
                       'bytes': len(data) - 2, 'sha256': digest(data), 'purpose': purpose})
    # Assembled regions and separately loaded files must not overlap.
    spans = sorted([(0x1010, len(sheets)), (ENTRY_ADDRESS, len(code))] +
                   [(int(a['address'][1:], 16), a['bytes']) for a in assets])
    for (start, size), (following, _) in zip(spans, spans[1:]):
        if start + size > following:
            raise ValueError(f'Overlap at ${following:04X}')
    output = build / 'xargon-wars.prg'
    output.write_bytes(LOAD_ADDRESS.to_bytes(2, 'little') + memory)

    obj = mos_hex(sources['OBJ'])
    assembled = {}
    for address in obj:
        if 0x1010 <= address < 0x1010 + len(sheets):
            assembled[address] = sheets[address - 0x1010]
        elif ENTRY_ADDRESS <= address < ENTRY_ADDRESS + len(code):
            assembled[address] = code[address - ENTRY_ADDRESS]
    for base, image in ((0x0002, 'zeropage.bin'), (0x033C, 'page3.bin')):
        data = (build / image).read_bytes()
        assembled.update({base + i: b for i, b in enumerate(data)})
    initialised = {a: b for a, b in obj.items() if a >= 0x1000}
    page_vars = {a: b for a, b in obj.items() if a < 0x1000}
    differences = [a for a, b in obj.items() if assembled.get(a) != b]
    manifest['used_modules'] = used
    manifest['unused_sources'] = sorted(set(sources) - set(used))
    manifest['assets'] = assets
    (build / 'recovery-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    report = {
        'load_address': f'${LOAD_ADDRESS:04X}', 'entry_address': f'${ENTRY_ADDRESS:04X}',
        'end_address': f'${END_ADDRESS - 1:04X}',
        'sheet_bytes': len(sheets), 'code_bytes': len(code),
        'output_bytes': output.stat().st_size, 'sha256': digest(output.read_bytes()),
        'object_listing_bytes': len(obj),
        'object_listing_initialised_bytes': len(initialised),
        'object_listing_low_memory_bytes': len(page_vars),
        'object_listing_differences': len(differences),
        'first_object_differences': [f'${a:04X}' for a in differences[:30]],
        'object_listing_range_matches': (min(initialised) == 0x1010 and
                                         max(page_vars) < 0x0400 and
                                         max(initialised) + 1 == ENTRY_ADDRESS + len(code)),
        'reference_sha256': digest(REFERENCE.read_bytes()) if REFERENCE.exists() else None,
        'reference_comparison': 'run scripts/compare_reference.py',
    }
    (build / 'comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if differences or not report['object_listing_range_matches']:
        raise ValueError('Assembled code differs from original OBJ listing')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    args = parser.parse_args()
    build_game(args.build_dir)
