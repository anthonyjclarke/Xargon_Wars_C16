#!/usr/bin/env python3
"""Check title, menu selection and gameplay entry on a PAL C16 in VICE.

The only scripted input is the menu's own joystick result: after REDJOS returns
inside MVEBOX, JMOVE is set to 1 and JFIRE to $80 with the box on PLAY GAME.
No instructions are patched and no jump bypasses the original control flow.
"""

import argparse
import json
import re
import subprocess
from pathlib import Path

from restore_c16 import ROOT, REFERENCE, ENTRY_ADDRESS, digest, tool

PASSES = 100  # further main-loop passes before the gameplay screenshot
VICE_ARGS = ['-default', '+saveres', '-model', 'c16pal', '-ramsize', '16', '+sound',
             '-initbreak', 'ready', '-limitcycles', '200000000']
# No warp: VICE skips rendering frames in warp mode, so screenshots could show a stale frame.


def run_monitor(build, stem, commands, extra=()):
    commands_file = build / (stem + '.mon')
    commands_file.write_text(commands)
    log = build / (stem + '-monitor.log')
    log.unlink(missing_ok=True)
    result = subprocess.run([tool('xplus4')] + VICE_ARGS + list(extra) + [
        '-moncommands', str(commands_file), '-logfile', str(build / (stem + '-vice.log')),
        '-monlog', '-monlogname', str(log)], cwd=str(build), capture_output=True, timeout=90)
    (build / (stem + '-console.log')).write_bytes(result.stdout + result.stderr)
    result.check_returncode()
    return log.read_text(errors='replace')


def labels_from(path):
    return {name: int(address, 16) for address, name in re.findall(
        r'^al ([0-9A-Fa-f]+) \.(\w+)$', path.read_text(), re.MULTILINE)}


def menu_check(code, labels):
    """Find LDA JMOVE immediately after JSR REDJOS in MVEBOX."""
    start = labels['MVEBOX'] - ENTRY_ADDRESS
    call = bytes((0x20, labels['REDJOS'] & 0xFF, labels['REDJOS'] >> 8))
    offset = code.find(call, start, start + 64)
    if offset < 0 or code[offset + 3:offset + 5] != bytes((0xA5, labels['JMOVE'])):
        raise ValueError('Cannot identify the original menu joystick test')
    return ENTRY_ADDRESS + offset + 3


def verify(build):
    build = build.resolve()
    labels = labels_from(build / 'xargon.labels')
    code = (build / 'code.bin').read_bytes()
    check = menu_check(code, labels)
    shots = {name: build / name for name in
             ('restored-title.png', 'restored-gameplay-start.png', 'restored-gameplay.png',
              'reference-title.png')}
    for path in list(shots.values()) + [build / 'gameplay-memory.bin', build / 'reference-memory.bin']:
        path.unlink(missing_ok=True)
    v = labels
    log = run_monitor(build, 'gameplay',
        f'load "{build / "xargon-wars.prg"}" 0\n'
        f'break {v["PARTY"]:x}\n'
        f'g {ENTRY_ADDRESS:x}\n'
        f'screenshot "{shots["restored-title.png"]}" 2\n'
        f'delete\n'
        f'> {v["YBOX"]:x} 00\n'
        f'break {check:x}\n'
        f'x\n'
        f'> {v["JMOVE"]:x} 01\n'
        f'> {v["JUP"]:x} 00 00 00\n'
        f'> {v["JFIRE"]:x} 80\n'
        f'delete\n'
        f'break {v["START"]:x}\n'
        f'x\n'
        f'screenshot "{shots["restored-gameplay-start.png"]}" 2\n'
        f'ignore 1 {PASSES:x}\n'
        f'x\n'
        f'screenshot "{shots["restored-gameplay.png"]}" 2\n'
        f'bsave "{build / "gameplay-memory.bin"}" 0 0000 3fff\n'
        f'quit\n')
    memory = (build / 'gameplay-memory.bin').read_bytes()
    state = {name: memory[v[name]] for name in
             ('PLAYIN', 'DEMO', 'LIVES', 'GLIVES', 'SHEETN', 'DEAD', 'FINITO', 'YBOX')}
    if (len(memory) != 0x4000 or state['PLAYIN'] != 1 or state['DEMO'] != 0
            or state['GLIVES'] != 3 or state['SHEETN'] != 0 or state['FINITO'] != 0):
        raise ValueError(f'Unexpected gameplay state: {state}')
    for address in (v['PARTY'], check, v['START']):
        if f'c:${address:04x}' not in log.lower():
            raise ValueError(f'VICE did not stop at ${address:04X}')
    for name in ('restored-title.png', 'restored-gameplay-start.png', 'restored-gameplay.png'):
        if not shots[name].read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError(f'Missing VICE screenshot: {name}')

    # The running PRG is a BASIC program (1 SYS7296). VICE autostart LOADs and RUNs it
    # from a virtual disk; stop at its title loop and check which snapshot-only bytes
    # the program itself recreates.
    comparison = json.loads((build / 'reference-comparison.json').read_text())
    reference = REFERENCE.read_bytes()
    ref_start = reference[0] | reference[1] << 8
    party = v['PARTY'] - 6  # PARTY follows the six-byte GIDO difference
    log = run_monitor(build, 'reference',
        f'break {party:x}\nx\n'
        f'screenshot "{shots["reference-title.png"]}" 2\n'
        f'bsave "{build / "reference-memory.bin"}" 0 0000 3fff\nquit\n',
        extra=('-autostart', str(REFERENCE)))
    if f'c:${party:04x}' not in log.lower():
        raise ValueError('Running PRG did not reach its title loop')
    running = (build / 'reference-memory.bin').read_bytes()
    recreated = []
    for item in comparison['runtime_state_differences']:
        address = int(item['address'][1:], 16)
        recreated.append({'address': item['address'], 'symbol': item['symbol'],
                          'snapshot': item['running'], 'at_title': f'${running[address]:02X}',
                          'recreated': running[address] == reference[2 + address - ref_start]})
    report = {
        'emulator': 'VICE xplus4 3.10', 'model': 'c16pal', 'ram_kib': 16, 'sound': 'off',
        'title_loop_reached': f'${v["PARTY"]:04X} PARTY',
        'menu_test_address': f'${check:04X} (LDA JMOVE after JSR REDJOS in MVEBOX)',
        'scripted_input': 'YBOX=0 (PLAY GAME), then JMOVE=1, JUP=JDOWN=0, JFIRE=$80 at the menu test',
        'gameplay_loop_reached': f'${v["START"]:04X} START, then {PASSES} further passes',
        'gameplay_state': state,
        'screenshots': [name for name in shots if name != 'reference-title.png'],
        'not_verified': ['manual keyboard and joystick play', 'sound', 'scoring over a full game',
                         'sheet transitions', 'death and game over', 'high-score entry',
                         'full play-through', 'real C16 or Plus/4 hardware'],
        'reference_start': 'VICE -autostart (LOAD and RUN from a virtual disk; BASIC SYS 7296)',
        'reference_title_loop_reached': f'${party:04X}',
        'reference_runtime_state_recreated_at_title': recreated,
        'reference_runtime_state_recreated_count':
            f'{sum(r["recreated"] for r in recreated)} of {len(recreated)}',
        'reference_sha256': digest(reference),
    }
    (build / 'vice-verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    verify(parser.parse_args().build_dir)
