#!/usr/bin/env python3
"""Probe isolated original routines in VICE without modifying game instructions.

A short caller in unused memory at $1B80 (SEI; CLD; LDA #a; LDY #y; JSR routine; NOP)
invokes a routine with controlled RAM, and memory is saved when it returns. Two further
probes only observe the running game. These are focused observations, not complete
gameplay, sound or hardware verification.
"""

import argparse
import json
import re
from pathlib import Path

from restore_c16 import ROOT, ENTRY_ADDRESS, digest
from verify_vice import labels_from, menu_check, run_monitor

CALLER = 0x1B80          # inside $1B02-$1BFF, which nothing assembles or loads
SCRPOS = 0x0C00 + 80 + 34  # five score digits on screen (SCORE-ROUTINES)
LIVES_DIGIT = 0x0C00 + 236


def hexbytes(data):
    return ' '.join(f'{b:02x}' for b in data)


class Session:
    """One VICE run holding several routine calls, each saved to its own capture."""

    def __init__(self, build, program, labels, name):
        self.build, self.labels, self.name = build, labels, name
        self.commands = [f'load "{program}" 0', f'break {CALLER + 9:x}']
        self.captures = []

    def call(self, case, routine, a=0, y=0, poke=None, screen=None):
        address = self.labels[routine] if isinstance(routine, str) else routine
        caller = [0x78, 0xD8, 0xA9, a, 0xA0, y, 0x20, address & 255, address >> 8, 0xEA]
        for target, values in (poke or {}).items():
            where = self.labels[target] if isinstance(target, str) else target
            self.commands.append(f'> {where:x} {hexbytes(values)}')
        if screen is not None:
            self.commands.append(f'> {SCRPOS:x} {hexbytes(screen.encode("ascii"))}')
        capture = self.build / f'{self.name}-{case}.bin'
        capture.unlink(missing_ok=True)
        self.commands += [f'> {CALLER:x} {hexbytes(caller)}', f'g {CALLER:x}',
                          f'bsave "{capture}" 0 0000 3fff']
        self.captures.append((case, capture))

    def run(self):
        log = run_monitor(self.build, self.name, '\n'.join(self.commands + ['quit']) + '\n')
        hits = log.lower().count(f'.c:{CALLER + 9:04x} ')
        if hits != len(self.captures):
            raise ValueError(f'{self.name}: {hits} of {len(self.captures)} calls returned')
        return {case: path.read_bytes() for case, path in self.captures}


def score_text(memory):
    return memory[SCRPOS:SCRPOS + 5].decode('ascii')


def probe(build):
    build = build.resolve()
    labels = labels_from(build / 'xargon.labels')
    program = build / 'xargon-wars.prg'
    output = build / 'rule-probes'
    output.mkdir(parents=True, exist_ok=True)
    checks = []

    # 1. Points per alien for each play-order sheet at level 0, and at level 1.
    session = Session(output, program, labels, 'points')
    cases = [(level, sheet) for sheet in range(16) for level in (0,)] + [(1, 0), (1, 15)]
    for level, sheet in cases:
        session.call(f'l{level}-s{sheet}', 'SCORE', screen='00000',
                     poke={'LEVEL': [level], 'SHEETN': [sheet], 'XTROB': [0], 'GLIVES': [3]})
    results = session.run()
    points = {f'level {lv} sheet {sh + 1}': int(score_text(results[f'l{lv}-s{sh}']))
              for lv, sh in cases}
    expected = {f'level 0 sheet {n}': (n if n < 9 else 10) for n in range(1, 17)}
    expected.update({'level 1 sheet 1': 10, 'level 1 sheet 16': 10})
    assert points == expected, points
    checks.append({'probe': 'points-per-alien', 'routine': 'SCORE', 'start_score': '00000',
                   'points': points})

    # 2. Extra life: XTRALI runs before the points are added.
    session = Session(output, program, labels, 'extra-life')
    state = {'LEVEL': [0], 'SHEETN': [0], 'XTROB': [0], 'GLIVES': [3], LIVES_DIGIT: [0x33]}
    session.call('first', 'SCORE', screen='00999', poke=state)
    session.call('second', 'SCORE')  # continue from the first call's memory
    results = session.run()
    sequence = []
    for case in ('first', 'second'):
        memory = results[case]
        sequence.append({'call': case, 'score_after': score_text(memory),
                         'GLIVES': memory[labels['GLIVES']], 'XTROB': memory[labels['XTROB']],
                         'lives_digit': chr(memory[LIVES_DIGIT])})
    assert [s['GLIVES'] for s in sequence] == [3, 4], sequence
    assert [s['score_after'] for s in sequence] == ['01000', '01001'], sequence
    checks.append({'probe': 'extra-life-after-1000', 'routine': 'SCORE twice, sheet 1, level 0',
                   'start_score': '00999', 'sequence': sequence})

    # 3. Overflow: adding 10 to 99999 at level 1.
    session = Session(output, program, labels, 'overflow')
    target = SCRPOS + 0xFF
    session.call('overflow', 'SCORE', screen='99999',
                 poke={'LEVEL': [1], 'SHEETN': [0], 'XTROB': [9], 'GLIVES': [3], target: [0x20]})
    memory = session.run()['overflow']
    stray = {'address': f'${target:04X}', 'row': (target - 0x0C00) // 40,
             'column': (target - 0x0C00) % 40, 'value': f'${memory[target]:02X}'}
    assert score_text(memory) == '00009' and memory[target] == 0x01, (score_text(memory), stray)
    checks.append({'probe': 'score-overflow', 'routine': 'SCORE at level 1 (+10)',
                   'start_score': '99999', 'score_after': score_text(memory),
                   'stray_store': stray, 'GLIVES': memory[labels['GLIVES']]})

    # 4. Level increase: each sheet's table values minus LEVEL, never below 1.
    session = Session(output, program, labels, 'levinc')
    levels = [0, 1, 3, 4, 7, 8, 20]
    for level in levels:
        session.call(f'level{level}', 'LEVINC',
                     poke={'LEVEL': [level], 'FRESPD': [8], 'MVESPD': [4], 'BOMSPD': [4]})
    results = session.run()
    speeds = [{'LEVEL': level, 'FRESPD': results[f'level{level}'][labels['FRESPD']],
               'MVESPD': results[f'level{level}'][labels['MVESPD']],
               'BOMSPD': results[f'level{level}'][labels['BOMSPD']]} for level in levels]
    assert [s['FRESPD'] for s in speeds] == [8, 7, 5, 4, 1, 1, 1], speeds
    assert [s['MVESPD'] for s in speeds] == [4, 3, 1, 1, 1, 1, 1], speeds
    checks.append({'probe': 'level-speed-reduction', 'routine': 'LEVINC',
                   'start': {'FRESPD': 8, 'MVESPD': 4, 'BOMSPD': 4}, 'results': speeds})

    # 5 and 6. Observe the running game: the Y register at CHSEL's KEYIT calls on the
    # title page, and the VICE clock between interrupt service entries in play.
    chsel = labels['CHSEL']
    keyit_calls = []
    code = (build / 'code.bin').read_bytes()
    call = bytes((0x20, labels['KEYIT'] & 255, labels['KEYIT'] >> 8))
    offset = chsel - ENTRY_ADDRESS
    for _ in range(2):
        offset = code.find(call, offset)
        keyit_calls.append(ENTRY_ADDRESS + offset)
        offset += 3
    commands = [f'load "{program}" 0', f'break {keyit_calls[0]:x}', f'g {ENTRY_ADDRESS:x}']
    commands += ['x'] * 5
    commands += ['delete', f'break {labels["PARTY"]:x}', 'x', 'delete',
                 f'> {labels["YBOX"]:x} 00', f'break {menu_check(code, labels):x}', 'x',
                 f'> {labels["JMOVE"]:x} 01', f'> {labels["JUP"]:x} 00 00 80', 'delete',
                 f'break {labels["START"]:x}', 'x', 'delete',
                 f'break {labels["PRSTAR"]:x}', f'break {labels["TIMER2"]:x}']
    commands += ['x'] * 24 + ['delete', f'break {labels["START"]:x}'] + ['x'] * 9 + ['quit']
    log = run_monitor(output, 'observe', '\n'.join(commands) + '\n')
    stops = re.findall(r'^\.C:([0-9a-f]{4}) .*? - A:([0-9A-F]{2}) X:([0-9A-F]{2}) Y:([0-9A-F]{2}) '
                       r'SP:\w+ \S+\s+(\d+)$', log, re.MULTILINE)
    keyit = [{'address': f'${int(a, 16):04X}', 'A': f'${acc}', 'X': f'${x}', 'Y': f'${y}'}
             for a, acc, x, y, _ in stops if int(a, 16) == keyit_calls[0]]
    raster = [int(c) for a, *_, c in stops if int(a, 16) == labels['PRSTAR']]
    loop = [int(c) for a, *_, c in stops if int(a, 16) == labels['START']][-9:]
    timer = [int(c) for a, *_, c in stops if int(a, 16) == labels['TIMER2']]
    assert len(keyit) >= 5 and len(raster) >= 3 and len(timer) >= 3, (len(keyit), raster, timer)
    checks.append({'probe': 'chsel-keyboard-row', 'routine': 'CHSEL first JSR KEYIT (J test)',
                   'source': 'CHSEL loads X=#$EF; KEYIT writes Y to $FD30 and $FF08',
                   'observed_registers': keyit[:6]})
    raster_gaps = [b - a for a, b in zip(raster, raster[1:])]
    timer_gaps = [b - a for a, b in zip(timer, timer[1:])]
    checks.append({'probe': 'interrupt-periods', 'unit': 'VICE CPU clock as printed by the monitor',
                   'raster_entries_PRSTAR': raster, 'timer2_entries_TIMER2': timer,
                   'raster_gaps': raster_gaps, 'timer2_gaps': timer_gaps,
                   'mean_raster_gap': round(sum(raster_gaps) / len(raster_gaps)),
                   'mean_timer2_gap': round(sum(timer_gaps) / len(timer_gaps)),
                   'timer2_before_raster': [r - max(t for t in timer if t < r)
                                            for r in raster if any(t < r for t in timer)],
                   'note': ('emulated time does not advance while the monitor is stopped; the '
                            'mechanism that keeps the two services in step is not established')})

    loop_gaps = [b - a for a, b in zip(loop, loop[1:])]
    assert len(loop_gaps) == 8, loop
    checks.append({'probe': 'main-loop-period', 'unit': 'VICE CPU clock as printed by the monitor',
                   'START_entries': loop, 'gaps': loop_gaps,
                   'mean_gap': round(sum(loop_gaps) / len(loop_gaps)),
                   'frames_per_pass': round(sum(loop_gaps) / len(loop_gaps) /
                                            (sum(raster_gaps) / len(raster_gaps)), 2),
                   'note': 'early in sheet 1 with no input; the pass length depends on the work done'})
    report = {
        'method': ('isolated routine calls from a caller at $1B80 (SEI, CLD) with controlled RAM, '
                   'plus breakpoint observations of the running game; no game instruction changed'),
        'prg_sha256': digest(program.read_bytes()), 'emulator': 'VICE xplus4, PAL C16, 16 KB',
        'scope': ('seven focused observations; not full gameplay, collision, sound, '
                  'concurrency or hardware verification'),
        'checks': checks,
    }
    (output / 'rule-probes.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    probe(parser.parse_args().build_dir)
