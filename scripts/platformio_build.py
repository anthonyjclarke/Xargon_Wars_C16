"""PlatformIO adapter for the same audited source build as build.sh."""

import subprocess
import sys
from pathlib import Path

from SCons.Script import Default, DefaultEnvironment

env = DefaultEnvironment()
root = Path(env.subst('$PROJECT_DIR'))
build = Path(env.subst('$BUILD_DIR'))
dependencies = list((root / 'scripts').glob('*.py')) + list((root / 'config').glob('*'))
dependencies += [p for p in (root / 'Original Source Recovered').rglob('*')
                 if p.is_file() and p.suffix.lower() not in ('.jpg', '.log') and p.name != '.DS_Store']


def assemble(source, target, env):
    subprocess.run([sys.executable, str(root / 'scripts/restore_c16.py'),
                    '--build-dir', str(build)], check=True, cwd=str(root))


def launch(source, target, env):
    subprocess.run([sys.executable, str(root / 'scripts/run_vice.py'),
                    str(build / 'xargon-wars.prg')], check=True, cwd=str(root))


program = env.Command(str(build / 'xargon-wars.prg'), [str(p) for p in dependencies],
                      env.VerboseAction(assemble, 'Assembling and checking original Xargon Wars source'))
env.Replace(PROGNAME='xargon-wars', PROGPATH=str(build / 'xargon-wars.prg'))
env.Alias('buildprog', program)
env.AddCustomTarget('upload', program, env.VerboseAction(launch, 'Launching Xargon Wars in VICE'),
                    title='Run in VICE', description='Run on an emulated 16 KB PAL C16')
Default(program)
