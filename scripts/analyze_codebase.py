#!/usr/bin/env python3
"""Generate the source/symbol index, code reference, asset data and glyph atlases.

Read-only analysis of the preserved disk sources and a previously verified build. It is
a static catalogue: direct transfers are those written as JSR/JMP/branch operands, not a
complete call graph, and byte spans are listing allocations, not function sizes.
"""

import argparse
import collections
import hashlib
import html
import json
import re
from pathlib import Path
from urllib.parse import quote

from restore_c16 import ROOT, ROOT_MODULE, ENTRY_ADDRESS, prepare_sources
from source_converter import OPCODES, convert, flatten, split_comment

REGIONS = [(0x1010, 'sheets.bin'), (ENTRY_ADDRESS, 'code.bin')]
BRANCHES = {'JSR', 'JMP', 'BCC', 'BCS', 'BEQ', 'BMI', 'BNE', 'BPL', 'BVC', 'BVS'}
WRITES = {'STA', 'STX', 'STY', 'INC', 'DEC', 'ASL', 'LSR', 'ROL', 'ROR'}


def table(headers, rows):
    rows = [[str(c).replace('|', '/') for c in row] for row in [headers] + rows]
    widths = [max(3, max(len(row[i]) for row in rows)) for i in range(len(headers))]
    if max(widths) > 45:
        raise ValueError(f'Markdown table cell exceeds 45 characters: {rows}')
    fmt = lambda row: '| ' + ' | '.join(v.ljust(widths[i]) for i, v in enumerate(row)) + ' |'
    rule = '|' + '|'.join(':' + '-' * (w + 1) for w in widths) + '|'
    return '\n'.join([fmt(rows[0]), rule] + [fmt(r) for r in rows[1:]])


def parse_line(line, macros=()):
    """Return (definition, statement, comment) for one original source line."""
    code, comment = split_comment(line)
    code = code.strip()
    definition = None
    if code and not code.startswith(('.', '*', ';')):
        equate = re.match(r'^([A-Z][A-Z0-9]*)\s*=\s*(.+)$', code)
        if equate:
            return equate[1], '=' + equate[2], comment.lstrip(';* ')
        first, *rest = code.split(None, 1)
        if first not in OPCODES | set(macros) and re.fullmatch(r'[A-Z][A-Z0-9]*', first):
            definition, code = first, (rest[0] if rest else '')
    return definition, code.strip(), comment.lstrip(';* ')


def evaluate(expression, values):
    """Evaluate an original operand expression strictly left to right (+, -, <, >)."""
    expression = expression.strip()
    part = None
    if expression[:1] in '<>':
        part, expression = expression[0], expression[1:]
    tokens = re.findall(r"\$[0-9A-F]+|%[01]+|\d+|[A-Z][A-Z0-9]*|[+\-*]|'.", expression)
    if ''.join(tokens) != expression.replace(' ', ''):
        raise ValueError(expression)
    total, operator = None, '+'
    for token in tokens:
        if token in '+-*' and total is not None:
            operator = token
            continue
        if token.startswith('$'):
            value = int(token[1:], 16)
        elif token.startswith('%'):
            value = int(token[1:], 2)
        elif token.isdigit():
            value = int(token)
        elif token.startswith("'"):
            value = ord(token[1])
        else:
            value = values[token]
        total = value if total is None else (total + value if operator == '+' else
                                             total - value if operator == '-' else total * value)
    if part == '<':
        total &= 0xFF
    elif part == '>':
        total = (total >> 8) & 0xFF
    return total


def statement_bytes(statement):
    """Recognise which statements emit bytes (for ownership classification only)."""
    word = statement.split(None, 1)[0].upper() if statement else ''
    return word in OPCODES or word in ('.BYTE', '.BYT', '.WORD')


def listing_owners(listing, source_map):
    """Map each emitted address to the original (module, line) that produced it."""
    rows = []
    lines = listing.read_text().splitlines()
    body = [l for l in lines if re.match(r'^[0-9A-F]{6}[ r] ', l)]
    index = 0
    for line in body:
        text = line[24:] if len(line) > 24 else ''
        has_bytes = bool(line[11:23].strip())
        if not text and has_bytes:
            continue  # continuation line of the previous statement
        if index == len(source_map) and not has_bytes:
            continue  # the listing's final empty line after the last newline
        rows.append((int(line[:6], 16), has_bytes, source_map[index]))
        index += 1
    if index != len(source_map):
        raise ValueError(f'Listing has {index} statements; generated source has {len(source_map)}')
    owners = {}
    starts = [(address, origin) for address, has_bytes, origin in rows if has_bytes]
    for (address, origin), (following, _) in zip(starts, starts[1:] + [(None, None)]):
        end = following if following is not None and following > address else 0x10000
        for region_start, region_size in REGION_SIZES:
            if region_start <= address < region_start + region_size:
                end = min(end, region_start + region_size)
                for a in range(address, end):
                    owners.setdefault(a, origin)
    return owners


def generated_source_map(lines):
    """Line i of the generated .s file -> (module, line) or None for generated lines."""
    mapping = [None, None, None]
    previous = None
    for name, number, line in lines:
        if name != previous:
            mapping.append(None)
            previous = name
        produced = len(convert([(name, number, line)]).splitlines()) - 4
        mapping += [(name, number)] * produced
    return mapping


def atlas(path, title, subtitle, data, start, mode, first_code=0, columns=16, names=None):
    """Decode glyph bits to SVG rectangles; colours are neutral index keys."""
    count = len(data) // 8
    cell_w, cell_h, scale = 64, 76, 5
    height = 80 + ((count + columns - 1) // columns) * cell_h
    keys = ['#111827', '#ef4444', '#38bdf8', '#fde047']
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{columns * cell_w + 20}" '
           f'height="{height}" viewBox="0 0 {columns * cell_w + 20} {height}">',
           '<rect width="100%" height="100%" fill="#f8fafc"/>',
           f'<text x="12" y="24" font-family="monospace" font-size="16">{html.escape(title)}</text>',
           f'<text x="12" y="46" font-family="monospace" font-size="12">{html.escape(subtitle)}</text>']
    for i in range(count):
        x, y = (i % columns) * cell_w + 12, (i // columns) * cell_h + 62
        for row, byte in enumerate(data[i * 8:i * 8 + 8]):
            if mode == 'multicolor':
                for col in range(4):
                    value = (byte >> (6 - col * 2)) & 3
                    out.append(f'<rect x="{x + col * scale * 2}" y="{y + row * scale}" '
                               f'width="{scale * 2}" height="{scale}" fill="{keys[value]}"/>')
            else:
                for col in range(8):
                    on = (byte >> (7 - col)) & 1
                    out.append(f'<rect x="{x + col * scale}" y="{y + row * scale}" width="{scale}" '
                               f'height="{scale}" fill="{"#e2e8f0" if on else "#111827"}"/>')
        label = names[i] if names else f'{first_code + i:03d} {start + i * 8:04X}'
        out.append(f'<text x="{x}" y="{y + 54}" font-family="monospace" font-size="10">'
                   f'{html.escape(label)}</text>')
    out.append('</svg>')
    path.write_text('\n'.join(out) + '\n')


REGION_SIZES = []


def analyze(build, output):
    output.mkdir(parents=True, exist_ok=True)
    sources, disk, manifest = prepare_sources(build / 'analysis-inputs')
    records = {f['name']: f for f in manifest['files']}
    labels = {name: int(address, 16) for address, name in re.findall(
        r'^al ([0-9A-Fa-f]+) \.(\w+)$', (build / 'xargon.labels').read_text(), re.MULTILINE)}
    lines = flatten(sources, ROOT_MODULE)
    used = list(dict.fromkeys(name for name, _, _ in lines))
    macros = {split_comment(l)[0].split()[1] for _, _, l in lines if l.startswith('.MAC ')}
    prg = (build / 'xargon-wars.prg').read_bytes()
    memory = bytearray(0x10000)
    memory[0x1010:0x1010 + len(prg) - 2] = prg[2:]
    global REGION_SIZES
    REGION_SIZES = [(start, len((build / name).read_bytes())) for start, name in REGIONS]
    source_map = generated_source_map(lines)
    if len(source_map) != len((build / 'xargon.s').read_text().splitlines()):
        raise ValueError('Generated source map does not match xargon.s')
    owners = listing_owners(build / 'xargon.lst', source_map)
    expected = {a for start, size in REGION_SIZES for a in range(start, start + size)}
    if set(owners) != expected:
        missing = sorted(expected - set(owners))
        raise ValueError(f'Listing ownership gap: {len(missing)} bytes from ${missing[0]:04X}' if missing else 'Listing ownership exceeds the regions')
    allocation = collections.Counter(module for module, _ in owners.values())

    # Definitions in assembly order, with addresses from the linker or from equates.
    definitions, order = {}, []
    for name, number, line in lines:
        definition, statement, comment = parse_line(line, macros)
        if not definition:
            continue
        kind = 'equate' if statement.startswith('=') else 'label'
        if kind == 'equate' and definition in definitions:
            definitions[definition]['repeated_at'] = f'{name}:{number}'
            continue
        if statement.startswith('*=*+'):
            kind = 'reserved'
        elif statement.upper().startswith(('.BYTE', '.WORD')):
            kind = 'data'
        definitions[definition] = {'symbol': definition, 'module': name, 'line': number,
                                   'address': labels.get(definition), 'kind': kind,
                                   'comment': comment,
                                   'expression': statement[1:].strip() if kind == 'equate' else None}
        order.append(definition)
    values = {s: d['address'] for s, d in definitions.items() if d['address'] is not None}
    for _ in range(4):
        for d in definitions.values():
            if d['kind'] == 'equate' and d['address'] is None:
                try:
                    d['address'] = values[d['symbol']] = evaluate(d['expression'], values)
                except (KeyError, ValueError):
                    pass
    # Labels are classified by the next statement in the same module.
    by_module = collections.defaultdict(list)
    for name, number, line in lines:
        by_module[name].append((number, line))
    for d in definitions.values():
        if d['kind'] != 'label':
            continue
        for number, line in by_module[d['module']]:
            if number < d['line']:
                continue
            _, statement, _ = parse_line(line, macros)
            if number == d['line'] and not statement:
                continue
            if statement:
                word = statement.split()[0]
                d['kind'] = ('instruction-label' if word in OPCODES | macros else
                             'data-label' if word.upper() in ('.BYTE', '.WORD') else
                             'reserved' if word.startswith('*=') else 'control-label')
                break
    # Byte spans to the next symbol in the same assembled region (layout, not size).
    placed = sorted((d['address'], s) for s, d in definitions.items()
                    if d['kind'] != 'equate' and d['address'] is not None)
    for (address, symbol), (following, _) in zip(placed, placed[1:] + [(None, None)]):
        definitions[symbol]['span_to_next_symbol'] = (following - address) if following else None

    transfers, writes = [], []
    for name, number, line in lines:
        _, statement, _ = parse_line(line, macros)
        parts = statement.split(None, 1)
        if len(parts) != 2:
            continue
        op, operand = parts[0], parts[1].strip()
        if op in BRANCHES:
            try:
                target = evaluate(operand, values)
            except (KeyError, ValueError):
                target = None
            base = re.match(r'^([A-Z][A-Z0-9]*)', operand)
            dest = definitions.get(base[1]) if base else None
            transfers.append({'module': name, 'line': number, 'operation': op, 'operand': operand,
                              'target_address': target,
                              'target_module': dest['module'] if dest else None})
        elif op in WRITES and not operand.startswith('('):
            target_text = operand.split(',')[0]
            try:
                target = evaluate(target_text, values)
            except (KeyError, ValueError):
                continue
            indexed = ',' in operand
            if ENTRY_ADDRESS <= target < 0x3AE6:
                owner = owners.get(target)
                origin = definitions.get(re.match(r'^([A-Z][A-Z0-9]*)', target_text)[1])
                if origin and origin['kind'] == 'instruction-label':
                    category = ('instruction-opcode' if target == origin['address']
                                else 'instruction-operand')
                else:
                    category = 'data-in-code'
            elif 0x3C00 <= target < 0x4000:
                category = 'character-set'
            elif 0x0800 <= target < 0x1000:
                category = 'screen-or-colour'
            elif target >= 0xFF00:
                category = 'ted-register'
            else:
                continue
            writes.append({'module': name, 'line': number, 'operation': op, 'operand': operand,
                           'target_address': target, 'indexed': indexed, 'category': category})

    variables = []
    for symbol in order:
        d = definitions[symbol]
        if d['module'] in ('VARS', 'EXTRA-MEMORY') and d['kind'] in ('data', 'reserved', 'data-label') \
                and d['address'] is not None and d['address'] < 0x1000:
            variables.append({'symbol': symbol, 'address': d['address'],
                              'bytes': d.get('span_to_next_symbol'), 'module': d['module'],
                              'line': d['line'], 'comment': d['comment']})
    # The last page-3 variable has no following symbol in its segment.
    for v in variables:
        if v['bytes'] is None or v['bytes'] > 0x200:
            v['bytes'] = 1 if v['module'] == 'VARS' else v['bytes']
    for v in variables:
        if v['module'] == 'VARS':
            region_end = 0x002E if v['address'] < 0x100 else 0x03B3
            v['bytes'] = min(v['bytes'], region_end - v['address'])
    extra_sizes = {'ALIENS': 96, 'BOMBTB': 32, 'BOMBPR': 32, 'BOMBCL': 32, 'STARTB': 32,
                   'ONTBL': 96, 'SAVECH': 160, 'ALICLS': 64, 'ALIPRT': 64}
    for v in variables:
        if v['symbol'] in extra_sizes:
            v['bytes'] = extra_sizes[v['symbol']]

    modules = []
    for name in sorted(sources):
        record = records[name]
        logical = sources[name][:-1] if sources[name] and sources[name][-1] == '' else sources[name]
        instructions = sum(1 for l in logical
                           if (lambda s: s and s.split()[0] in OPCODES | macros)(parse_line(l, macros)[1]))
        modules.append({'name': name, 'extracted_copy': record['extracted_copy'],
                        'disk_bytes': record['bytes'], 'sha256': record['sha256'],
                        'logical_lines': len(logical), 'instruction_lines': instructions,
                        'prg_bytes_allocated': allocation.get(name, 0),
                        'in_main_assembly': name in used,
                        'assembly_position': used.index(name) + 1 if name in used else None})

    referenced = set()
    for name, number, line in lines:
        _, statement, _ = parse_line(line, macros)
        if statement.startswith('='):
            operand = statement[1:]
        else:
            operand = statement.split(None, 1)[1] if len(statement.split(None, 1)) == 2 else ''
        referenced.update(re.findall(r"(?<!')\b[A-Z][A-Z0-9]*\b", re.sub(r"'[^']*'", '', operand)))
    unreferenced = [s for s in order if s not in referenced and definitions[s]['module'] in used]
    symbols = sorted((definitions[s] for s in order if definitions[s]['module'] in used),
                     key=lambda d: (used.index(d['module']), d['line']))
    data = {
        'method': ('static catalogue of the ULTRA assembly: listing-derived byte ownership, '
                   'source-defined symbols, direct transfers written as operands, and '
                   'write instructions to code, character-set, screen and TED addresses. '
                   'Not a complete call graph, cycle profile or data-flow analysis.'),
        'source_image_sha256': manifest['image_sha256'],
        'prg_sha256': hashlib.sha256(prg).hexdigest(),
        'assembly_order': used, 'modules': modules, 'symbols': symbols,
        'variables': variables, 'direct_transfers': transfers, 'notable_writes': writes,
        'unreferenced_symbols': unreferenced,
        'byte_owner_ranges': [], 'counts': {}}
    current = None
    for address in sorted(owners):
        module, number = owners[address]
        if current and current['module'] == module and current['end'] + 1 == address:
            current['end'] = address
        else:
            current = {'start': address, 'end': address, 'module': module, 'first_line': number}
            data['byte_owner_ranges'].append(current)
    data['counts'] = {
        'disk_source_files': len(sources), 'main_assembly_modules': len(used),
        'main_logical_lines': sum(m['logical_lines'] for m in modules if m['in_main_assembly']),
        'main_instruction_lines': sum(m['instruction_lines'] for m in modules if m['in_main_assembly']),
        'symbols_defined': len(symbols),
        'instruction_labels': sum(1 for s in symbols if s['kind'] == 'instruction-label'),
        'equates': sum(1 for s in symbols if s['kind'] == 'equate'),
        'direct_transfers': len(transfers),
        'jsr_sites': sum(1 for t in transfers if t['operation'] == 'JSR'),
        'notable_writes': len(writes),
        'unreferenced_symbols': len(unreferenced),
        'instruction_operand_writes': sum(1 for w in writes if w['category'] == 'instruction-operand'),
        'instruction_opcode_writes': sum(1 for w in writes if w['category'] == 'instruction-opcode'),
        'character_set_writes': sum(1 for w in writes if w['category'] == 'character-set'),
        'prg_assembled_bytes': len(owners),
        'zero_page_bytes': sum(v['bytes'] for v in variables if v['address'] < 0x100),
        'page3_bytes': sum(v['bytes'] for v in variables if 0x300 <= v['address'] < 0x400)}
    (output / 'codebase-index.json').write_text(json.dumps(data, indent=2) + '\n')

    write_reference(output, data, definitions, used, records)
    assets = export_assets(output, memory, labels, values, disk)
    font = bytes(memory[0x3C00:0x4000])
    atlas(output / 'font-hires.svg', 'FRAK! character set, codes 000-127, one bit per pixel',
          'Raw glyph bytes at $3C00; neutral colours, not the TED palette.', font, 0x3C00, 'hires')
    atlas(output / 'font-multicolor.svg', 'FRAK! character set, codes 000-127, two bits per pixel',
          'Index keys 0-3 = background, MULTI1, MULTI2, cell colour; not the TED palette.',
          font, 0x3C00, 'multicolor')
    alien = b''
    names = []
    for sheet in assets['sheets']:
        alien += bytes.fromhex(sheet['alien_glyphs']['hex'])
        names += [f'T{sheet["table_index"]:X} f{f} c{c}' for f in range(3) for c in range(3)]
    atlas(output / 'alien-glyphs.svg', 'Alien glyph data for the 16 sheet tables (3 frames x 3 cells)',
          'Two bits per pixel; T = SHTABLE entry, f = frame, c = cell (codes 101-103).',
          alien, 0, 'multicolor', columns=9, names=names)
    print(json.dumps(data['counts'], indent=2))
    print(f'Wrote {output}')


def write_reference(output, data, definitions, used, records):
    modules = {m['name']: m for m in data['modules']}
    text = ['# Generated Code Reference', '', '## Scope and Method', '',
            'Generated by `scripts/analyze_codebase.py` from the verified build and the preserved '
            'disk sources. Line numbers are the logical lines of each disk file (CR-separated, '
            'counting from 1). PRG bytes are allocated from the assembler listing, so a module '
            'total includes code, tables and text; it is not a function size. Direct transfers '
            'are operands written in JSR, JMP and branch instructions: fall-through, interrupt '
            'vectors, the `WHJUMP` computed branch and runtime operand patches are not in that '
            'list. A symbol can name a branch point or data, not only a callable routine.', '',
            '---', '', '## Modules in Assembly Order', '',
            table(['Module', 'PRG bytes', 'Lines', 'Instr. lines'],
                  [(f'`{n}`', modules[n]['prg_bytes_allocated'], modules[n]['logical_lines'],
                    modules[n]['instruction_lines']) for n in used]), '',
            'Other disk source files, not assembled into the game: ' +
            ', '.join(f'`{m["name"]}`' for m in data['modules'] if not m['in_main_assembly']) + '.',
            '', '---', '', '## Source Locations', '']
    for m in data['modules']:
        text.append(f"`{m['name']}` – [disk file](../../{quote(m['extracted_copy'], safe='/')}); "
                    f"{m['disk_bytes']} bytes, {m['logical_lines']} logical lines.")
        text.append('')
    text += ['---', '', '## Variables', '',
             'Zero page and page 3 come from `VARS`; the larger tables at `$0400` and `$0560` '
             'come from `EXTRA-MEMORY`. Sizes are the declared reservation or the distance to '
             'the next variable.', '',
             table(['Symbol', 'Address', 'Bytes', 'Comment'],
                   [(f"`{v['symbol']}`", f"`${v['address']:04X}`", v['bytes'], v['comment'][:30])
                    for v in data['variables']]), '',
             '---', '', '## Writes into Code and Graphics', '',
             'Every write instruction whose operand resolves into the program code, the '
             'character set or a TED register. `instruction-operand` and `instruction-opcode` mark '
             'self-modifying code; `data-in-code` marks variables and text kept between routines.', '',
             table(['Site', 'Instruction', 'Target', 'Category'],
                   [(f"`{w['module']}:{w['line']}`", f"`{w['operation']} {w['operand']}`"[:45],
                     f"`${w['target_address']:04X}`", w['category'])
                    for w in data['notable_writes'] if w['category'] != 'ted-register']), '',
             '---', '', '## Symbols Never Used as an Operand', '',
             'Defined in the assembled source but never named in an instruction operand, data '
             'expression or equate. Labels on instructions can still be reached by falling through '
             'from the line above.', '',
             ', '.join(f'`{s}`' for s in data['unreferenced_symbols']) + '.', '',
             '---', '', '## Symbols by Module', '']
    for name in used:
        rows = [s for s in data['symbols'] if s['module'] == name]
        if not rows:
            continue
        text += [f'### {name}', '',
                 table(['Symbol', 'Address', 'Line', 'Kind'],
                       [(f"`{s['symbol']}`", f"`${s['address']:04X}`" if s['address'] is not None
                         else 'unresolved', s['line'], s['kind']) for s in rows]), '']
    (output / 'CODE_REFERENCE.md').write_text('\n'.join(text).rstrip() + '\n')


def export_assets(output, memory, labels, values, disk):
    def raw(symbol, length):
        address = labels[symbol]
        return {'symbol': symbol, 'address': address, 'bytes': length,
                'hex': bytes(memory[address:address + length]).hex()}

    sheet_fields = ['movement_length', 'movement_data_lo', 'movement_data_hi', 'animation_speed',
                    'firing_speed', 'multi_colour_1', 'multi_colour_2', 'alien_attribute',
                    'movement_speed', 'glyph_data_lo', 'glyph_data_hi', 'positions_lo',
                    'positions_hi', 'alien_count', 'bomb_speed', 'spare']
    order = list(memory[labels['CONSHT']:labels['CONSHT'] + 16])
    sheets = []
    for index in range(16):
        entry = memory[0x1010 + index * 16:0x1010 + index * 16 + 16]
        fields = dict(zip(sheet_fields, entry))
        movement = fields['movement_data_lo'] | fields['movement_data_hi'] << 8
        glyphs = fields['glyph_data_lo'] | fields['glyph_data_hi'] << 8
        positions = fields['positions_lo'] | fields['positions_hi'] << 8
        count = fields['alien_count']
        sheets.append({
            'table_index': index, 'play_order': order.index(index) + 1,
            'fields': fields, 'entry_hex': bytes(entry).hex(),
            'movement': {'address': movement, 'directions': list(
                memory[movement:movement + fields['movement_length']])},
            'initial_positions': {'address': positions, 'triples': [
                list(memory[positions + 3 * i:positions + 3 * i + 3]) for i in range(count)]},
            'alien_glyphs': {'address': glyphs, 'bytes': 72,
                             'hex': bytes(memory[glyphs:glyphs + 72]).hex()}})
    tables = {}
    for symbol, length in [('CONSHT', 16), ('XTBL', 9), ('YTBL', 9), ('SCRPTR', 50), ('YCOL', 7),
                           ('TIME24', 4), ('FICHAR', 16), ('EXPLAN', 72), ('LACHAR', 16),
                           ('TTB', 44), ('SHDAY', 7), ('STCOL', 4), ('SPPIX', 4), ('STOP', 4),
                           ('GACOUL', 12), ('PLOXEL', 4), ('BOXTBL', 29), ('HISTBL', 99),
                           ('BANNER', 15), ('MENTBL', 85), ('TEXT', 65), ('CLRMES', 19),
                           ('GAMMES', 32), ('SROLBF', 255), ('TESCO', 44), ('TIM11', 4),
                           ('BTD', 5), ('RWD', 5), ('MVEPAT', 2), ('SNTB', 7), ('KST', 8),
                           ('JST', 8), ('EXCHR', 3), ('HOFSET', 6), ('SCROFT', 12),
                           ('STRIN', 6), ('SCRBUF', 5)]:
        tables[symbol] = raw(symbol, length)
    letters = {}
    for symbol in ('XDATA', 'ADATA', 'RDATA', 'GDATA', 'ODATA', 'NDATA', 'WDATA', 'SDATA'):
        address, points = labels[symbol], []
        while memory[address] != 0xFF:
            points.append([memory[address], memory[address + 1]])
            address += 2
        letters[symbol] = {'address': labels[symbol], 'points': points}
    music = disk['MUSIC/CODE'].data
    assets = {
        'note': ('Raw bytes from the verified build; addresses are integers. Colours are TED '
                 'attribute bytes ((luminance << 4) | colour); see graphics/ted-palette.json.'),
        'font': {'source': 'FRAK!', 'address': 0x3C00, 'glyphs': 128,
                 'hex': bytes(memory[0x3C00:0x4000]).hex()},
        'tune': {'source': 'MUSIC/CODE', 'address': 0x1C00, 'bytes': 128,
                 'hex': music[2:].hex(), 'layout': 'three bytes per note: TED frequency lo, hi, length; $FF length ends'},
        'sheet_table': {'address': 0x1010, 'entry_bytes': 16, 'fields': sheet_fields},
        'sheets': sheets, 'tables': tables, 'title_letters': letters,
        'runtime_glyph_addresses': {k: values[k] for k in ('ALCHAR', 'EXCHAR', 'ALBULC', 'LAXCHR',
                                                           'CHARS', 'CHARX')}}
    (output / 'asset-data.json').write_text(json.dumps(assets, indent=1) + '\n')
    return assets


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'docs/analysis')
    args = parser.parse_args()
    analyze(args.build_dir.resolve(), args.output_dir.resolve())
