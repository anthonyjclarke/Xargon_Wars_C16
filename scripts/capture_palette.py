#!/usr/bin/env python3
"""Capture the 128-entry TED palette that VICE uses for this project's screenshots.

A fresh PAL C16 shows the ROM reverse space ($A0) in 128 cells whose attributes are
$00-$7F. A short delay loop at $1000 lets VICE draw the frame, then the screenshot is
sampled at each cell centre. Needs Pillow 10.1 or later.
"""

import argparse
import json
from pathlib import Path

from PIL import Image

from restore_c16 import ROOT
from verify_vice import run_monitor

DELAY = [0x78, 0xA2, 0x00, 0xA0, 0x00, 0x88, 0xD0, 0xFD, 0xCA, 0xD0, 0xF8, 0xEA]


def capture(build, output):
    build.mkdir(parents=True, exist_ok=True)
    shot = build / 'palette.png'
    shot.unlink(missing_ok=True)
    colours = ' '.join(f'{c:02x}' for c in range(128))
    commands = ['> ff19 00', '> ff15 00', 'f 0c00 0fe7 20', 'f 0c00 0c7f a0',
                f'> 0800 {colours}', f'> 1000 {" ".join(f"{b:02x}" for b in DELAY)}',
                f'break {0x1000 + len(DELAY) - 1:x}', 'g 1000', 'g 1000',
                f'screenshot "{shot}" 2', 'quit']
    run_monitor(build, 'palette', '\n'.join(commands) + '\n')
    image = Image.open(shot).convert('RGB')
    # Locate the text window: the first cell holds colour $00 (black on black), so
    # find the left/top edge from the first non-black pixel of cell 1 ($01 white).
    pixels = image.load()
    width, height = image.size
    first = next((x, y) for y in range(height) for x in range(width) if pixels[x, y] != (0, 0, 0))
    left, top = first[0] - 8, first[1]
    palette = []
    for index in range(128):
        x = left + (index % 40) * 8 + 4
        y = top + (index // 40) * 8 + 4
        palette.append(list(pixels[x, y]))
    assert palette[0x00] == [0, 0, 0] and palette[0x71] == [255, 255, 255], palette[:2]
    data = {'source': 'VICE 3.10 xplus4 default palette, captured from a screenshot',
            'method': __doc__.strip().splitlines()[1].strip(),
            'window_origin': [left, top], 'screenshot_size': [width, height],
            'index': 'TED attribute low 7 bits: (luminance << 4) | colour',
            'rgb': palette}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(data, indent=1) + '\n')
    print(f'Wrote {output}: window at {left},{top}')
    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build-dir', type=Path, default=ROOT / 'build/palette')
    parser.add_argument('--output', type=Path, default=ROOT / 'docs/analysis/graphics/ted-palette.json')
    args = parser.parse_args()
    capture(args.build_dir.resolve(), args.output.resolve())
