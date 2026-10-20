#!/usr/bin/env python3
"""Compare the source build with the supplied running PRG and explain every difference.

Both files are uncompressed saved-address PRG images, so their memory can be compared
directly. The running version is then reproduced by assembling the source with the
documented revision edits in ALIENS; that variant exists only for this comparison.
"""

import argparse
import json
import re
from pathlib import Path

from restore_c16 import (ROOT, REFERENCE, ENTRY_ADDRESS, ROOT_MODULE, DISK_ASSETS,
                         assemble, build_game, digest, prepare_sources)

# (module, line, exact original text, replacement lines) -- the running revision.
RUNNING_REVISION_EDITS = [
    ('ALIENS', 150, 'LDA IH', []),
    ('ALIENS', 151, 'AND #$F    ;* 0 - 15', []),
    ('ALIENS', 152, 'STA IH', []),
    ('ALIENS', 227, 'AND #$0F', ['AND #$7F']),
]


def image(path):
    data = path.read_bytes()
    memory = bytearray(0x10000)
    start = data[0] | data[1] << 8
    memory[start:start + len(data) - 2] = data[2:]
    return memory, start, start + len(data) - 2


def running_variant(build, sources):
    """Assemble the source with RUNNING_REVISION_EDITS applied, in a separate directory."""
    edited = {name: list(lines) for name, lines in sources.items()}
    for module, line, original, replacement in RUNNING_REVISION_EDITS:
        if edited[module][line - 1] != original:
            raise ValueError(f'{module}:{line} is not {original!r}')
    for module, line, _, replacement in sorted(RUNNING_REVISION_EDITS, key=lambda e: -e[1]):
        edited[module][line - 1:line] = replacement
    variant = build / 'running-variant'
    variant.mkdir(parents=True, exist_ok=True)
    assemble(variant, edited, ROOT_MODULE, 'xargon', ROOT / 'config/c16.cfg')
    return (variant / 'sheets.bin').read_bytes(), (variant / 'code.bin').read_bytes()


WRITE = re.compile(r'^(?:\w+:\s*)?(?:STA|STX|STY|INC|DEC|ASL|LSR|ROL|ROR)\s+(\w+)(\+\d+)?(,[XY])?',
                   re.IGNORECASE)


def runtime_written(build_dir, addresses):
    """Name each address and show the source instruction that writes it at run time."""
    labels = sorted((int(a, 16), n) for a, n in re.findall(
        r'^al ([0-9A-F]+) \.(\w+)$', (build_dir / 'xargon.labels').read_text(), re.MULTILINE))
    writers = {}
    for line in (build_dir / 'xargon.s').read_text().splitlines():
        match = WRITE.match(line.split(';')[0].strip())
        if match:
            name, offset, index = match[1], int(match[2] or 0), match[3]
            writers.setdefault(name, []).append((offset, bool(index), line.split(';')[0].strip()))
    result = []
    for address in addresses:
        base, name = max((a, n) for a, n in labels if a <= address)
        offset = address - base
        evidence = [text for o, indexed, text in writers.get(name, []) if o == offset or indexed]
        result.append({'address': f'${address:04X}', 'symbol': f'{name}+{offset}' if offset else name,
                       'written_by': evidence[:3]})
    return result


def runs(addresses):
    spans = []
    for address in addresses:
        if spans and spans[-1][1] + 1 == address:
            spans[-1][1] = address
        else:
            spans.append([address, address])
    return [f'${a:04X}-${b:04X}' if a != b else f'${a:04X}' for a, b in spans]


def compare(build):
    build = build.resolve()
    if not (build / 'xargon-wars.prg').exists():
        build_game(build)
    sources, disk, _ = prepare_sources(build / 'reference-inputs')
    ours, our_start, our_end = image(build / 'xargon-wars.prg')
    ref, ref_start, ref_end = image(REFERENCE)
    code = (build / 'code.bin').read_bytes()
    code_end = ENTRY_ADDRESS + len(code)
    variant_sheets, variant_code = running_variant(build, sources)
    variant_end = ENTRY_ADDRESS + len(variant_code)

    def region(name, start, end, note):
        covered = range(start, min(end, ref_end))
        changed = [a for a in covered if ours[a] != ref[a]]
        return {'region': name, 'range': f'${start:04X}-${end - 1:04X}', 'bytes': end - start,
                'bytes_in_running_prg': len(covered), 'differences': len(changed), 'note': note}

    music = dict((n, a) for n, a, _ in DISK_ASSETS)
    regions = [
        {'region': 'BASIC stub', 'range': f'${ref_start:04X}-$100F', 'bytes': 0x1010 - ref_start,
         'differences': None, 'stub_hex': ref[ref_start:0x1010].hex(),
         'note': 'only in the running PRG: line 1 SYS 7296 ($1C80); not in any source file'},
        region('Sheet tables', 0x1010, 0x1010 + len(variant_sheets), 'SHTABLE and SHEET1-SHEETG'),
        region('Gap after sheets', 0x1010 + len(variant_sheets), music['MUSIC/CODE'],
               'never assembled; the build leaves zeros, the running PRG has $00 then $FF fill'),
        region('Tune table', 0x1C00, 0x1C80, 'disk file MUSIC/CODE'),
        region('Program code', ENTRY_ADDRESS, code_end, 'raw comparison; see revision analysis'),
        region('After source code', code_end, music['FRAK!'], 'build leaves zeros'),
        region('Character set', 0x3C00, 0x4000, "disk file FRAK!"),
    ]
    state = [ENTRY_ADDRESS + i for i, b in enumerate(variant_code) if ref[ENTRY_ADDRESS + i] != b]
    runtime = runtime_written(build / 'running-variant', state)
    unexplained = [r['address'] for r in runtime if not r['written_by']]
    font = [a for a in range(0x3C00, ref_end) if ours[a] != ref[a]]
    variant_matches = (not unexplained and
                       bytes(ref[0x1010:0x1010 + len(variant_sheets)]) == variant_sheets)
    residue = [a for a in range(variant_end, 0x3C00) if ref[a] not in (0x00, 0xFF)]
    report = {
        'format': 'both are uncompressed saved-address PRG images; compared as memory',
        'reference': str(REFERENCE.relative_to(ROOT)), 'reference_sha256': digest(REFERENCE.read_bytes()),
        'reference_load': f'${ref_start:04X}', 'reference_end': f'${ref_end - 1:04X}',
        'build_load': f'${our_start:04X}', 'build_end': f'${our_end - 1:04X}',
        'regions': regions,
        'source_code_end': f'${code_end - 1:04X}', 'running_code_end': f'${variant_end - 1:04X}',
        'running_revision_edits': [
            {'module': m, 'line': n, 'source': o, 'running': r} for m, n, o, r in RUNNING_REVISION_EDITS],
        'running_revision_reproduced': variant_matches,
        'running_revision_method': ('assemble source with the edits above; every remaining code '
                                    'difference must be a location the program itself writes'),
        'runtime_state_differences': [
            dict(r, source=f'${variant_code[int(r["address"][1:], 16) - ENTRY_ADDRESS]:02X}',
                 running=f'${ref[int(r["address"][1:], 16)]:02X}') for r in runtime],
        'unexplained_code_differences': unexplained,
        'character_set_differences': {
            'addresses': runs(font),
            'disk': bytes(ours[font[0]:font[-1] + 1]).hex() if font else '',
            'running': bytes(ref[font[0]:font[-1] + 1]).hex() if font else '',
            'glyphs': sorted({(a - 0x3C00) // 8 for a in font}),
            'missing_from_running_prg': [f'${a:04X}' for a in range(ref_end, 0x4000)],
            'note': 'FRAK! glyph bytes that differ from the disk file; see the validation report'},
        'running_variant_code_sha256': digest(variant_code),
        'residue_after_running_code': {
            'non_fill_bytes': len(residue), 'ranges': runs(residue),
            'note': ('inference: left in memory by an earlier, longer assembly (the strings end '
                     '12 bytes later and a key-scanning routine follows); not reproduced by the '
                     'build and not part of either revision')},
    }
    (build / 'reference-comparison.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    if not variant_matches:
        raise ValueError('Documented revision edits do not reproduce the running PRG code')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    compare(parser.parse_args().build_dir)
