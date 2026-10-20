#!/usr/bin/env python3
"""Run the rebuilt Xargon Wars, or the supplied running PRG, on a 16 KB PAL C16 in VICE."""

import argparse
import subprocess
from pathlib import Path

from restore_c16 import ROOT, REFERENCE, ENTRY_ADDRESS, tool

MACHINE = ['-default', '+saveres', '-model', 'c16pal', '-ramsize', '16']


def launch(program, entry=ENTRY_ADDRESS, original=False):
    program = program.resolve(strict=True)
    build = ROOT / 'build/vice'
    build.mkdir(parents=True, exist_ok=True)
    if original:
        # The supplied PRG is a BASIC program (1 SYS7296): load and RUN it as a user would.
        arguments = ['-autostart', str(program)]
    else:
        # The rebuild is a saved-address machine-code image with no BASIC stub.
        commands = build / 'start.mon'
        commands.write_text(f'load "{program.as_posix()}" 0\ng {entry:x}\n')
        arguments = ['-initbreak', 'ready', '-moncommands', str(commands)]
    with (build / 'console.log').open('w') as log:
        process = subprocess.Popen([tool('xplus4')] + MACHINE + arguments +
                                   ['-logfile', str(build / 'vice.log')],
                                   cwd=str(build), stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
    print(f'VICE started (PID {process.pid}): {program}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('program', nargs='?', type=Path, default=ROOT / 'build/xargon-wars.prg')
    parser.add_argument('--original', action='store_true', help='LOAD and RUN the supplied running PRG')
    parser.add_argument('--entry', type=lambda s: int(s, 0), default=ENTRY_ADDRESS)
    args = parser.parse_args()
    launch(REFERENCE if args.original else args.program, args.entry, args.original)
