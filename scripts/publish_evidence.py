#!/usr/bin/env python3
"""Copy checked build evidence into docs/ and record the tool versions that produced it.

Run after `make verify` and `make test`. Only JSON reports and screenshots are copied;
the build directory itself stays out of Git.
"""

import argparse
import json
import platform
import re
import shutil
import subprocess
from pathlib import Path

from restore_c16 import ROOT, tool

REPORTS = {'comparison.json': 'build-comparison.json',
           'reference-comparison.json': 'reference-comparison.json',
           'recovery-manifest.json': 'source-manifest.json',
           'vice-verification.json': 'vice-verification.json'}
SCREENSHOTS = ['restored-title.png', 'restored-gameplay-start.png', 'restored-gameplay.png',
               'reference-title.png']


def version(command, pattern):
    result = subprocess.run(command, capture_output=True, text=True)
    match = re.search(pattern, result.stdout + result.stderr)
    return match[1] if match else 'unknown'


def publish(build, tests_passed, date):
    verification = ROOT / 'docs/verification'
    images = ROOT / 'docs/images'
    verification.mkdir(parents=True, exist_ok=True)
    images.mkdir(parents=True, exist_ok=True)
    for source, target in REPORTS.items():
        text = (build / source).read_text().replace(str(build), 'build').replace(str(ROOT) + '/', '')
        (verification / target).write_text(text)
    for name in SCREENSHOTS:
        shutil.copyfile(build / name, images / name)
    vice_log = (build / 'gameplay-vice.log').read_text(errors='replace')
    comparison = json.loads((build / 'comparison.json').read_text())
    tools = {
        'date': date,
        'regression_tests_passed': tests_passed,
        'python': platform.python_version(),
        'ca65_reported_version': version([tool('ca65'), '--version'], r'(V[\d.]+)'),
        'ld65_reported_version': version([tool('ld65'), '--version'], r'(V[\d.]+)'),
        'vice_version': (re.search(r'VICE Version ([\d.]+)', vice_log) or [None, 'unknown'])[1],
        'platformio_core': version(['pio', '--version'], r'version ([\d.]+)'),
        'output_sha256': comparison['sha256'],
        'object_listing_differences': comparison['object_listing_differences'],
        'github_workflow': 'see docs/SOURCE_AND_VALIDATION.md for the recorded CI result',
    }
    (verification / 'tool-checks.json').write_text(json.dumps(tools, indent=2) + '\n')
    print(json.dumps(tools, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build')
    parser.add_argument('--tests-passed', type=int, required=True)
    parser.add_argument('--date', required=True, help='date of the verification run, YYYY-MM-DD')
    args = parser.parse_args()
    publish(args.build_dir.resolve(), args.tests_passed, args.date)
