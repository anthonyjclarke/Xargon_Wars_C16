#!/usr/bin/env python3
"""Reconstruct explanatory graphics from Xargon Wars' exported original bytes.

Requires Pillow 10.1 or later. Reads docs/analysis/asset-data.json, the captured VICE
palette docs/analysis/graphics/ted-palette.json and the verified gameplay screenshot.
This decodes glyphs and tables into figures; it is not a TED or raster emulator.
"""

import argparse
import hashlib
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / 'docs/analysis'
INK, MUTED, PAPER, BLUE, LINE = '#142c45', '#52677c', '#f4f7fb', '#1768a4', '#bdcbd9'
SHIP_ROWS = [[32, 80, 32], [81, 82, 83], [84, 85, 86]]   # SHDAY: +1, +40..42, +80..82
FRAME_ORDER = [0, 1, 2, 1]                                # TIME24: 0, 24, 48, 24
GIF_MS = 160


def digest(data):
    return hashlib.sha256(data).hexdigest()


def font(size=18):
    return ImageFont.load_default(size=size)


def label(im, xy, text, size=18, fill=INK):
    ImageDraw.Draw(im).text(xy, text, font=font(size), fill=fill)


def canvas(title, subtitle, height, width=1200):
    im = Image.new('RGB', (width, height), PAPER)
    label(im, (32, 22), title, 30)
    label(im, (32, 64), subtitle, 17, MUTED)
    ImageDraw.Draw(im).line((32, 98, width - 32, 98), fill=LINE, width=2)
    return im


def enlarged(im, scale):
    return im.resize((im.width * scale, im.height * scale), Image.Resampling.NEAREST)


class Graphics:
    def __init__(self, assets, palette):
        self.assets, self.palette = assets, palette
        self.font = bytes.fromhex(assets['font']['hex'])
        assert len(self.font) == 1024
        self.tables = {k: bytes.fromhex(v['hex']) for k, v in assets['tables'].items()}

    def bank(self, sheet=None, frame=0):
        """FRAK! with the runtime glyph changes ANICHR makes for one frame and sheet."""
        bank = bytearray(self.font)
        if sheet is not None:
            glyphs = bytes.fromhex(sheet['alien_glyphs']['hex'])
            offset = (0, 24, 48, 24)[frame]
            bank[0x3F28 - 0x3C00:0x3F40 - 0x3C00] = glyphs[offset:offset + 24]        # 101-103
            bank[0x3F48 - 0x3C00:0x3F60 - 0x3C00] = self.tables['EXPLAN'][offset:offset + 24]  # 105-107
        half = (frame & 1) * 8
        bank[0x3F40 - 0x3C00:0x3F48 - 0x3C00] = self.tables['FICHAR'][half:half + 8]   # bomb, 104
        bank[0x3EE0 - 0x3C00:0x3EE8 - 0x3C00] = self.tables['LACHAR'][half:half + 8]   # laser, 92
        return bank

    def render(self, rows, bank, attribute, multi=(0, 0), background=0):
        """TED character cell: attribute bit 3 selects multicolour; pens bg, MULTI1, MULTI2, cell."""
        out = Image.new('RGB', (len(rows[0]) * 8, len(rows) * 8))
        attributes = attribute if isinstance(attribute, list) else [[attribute] * len(rows[0])] * len(rows)
        for r, row in enumerate(rows):
            for c, code in enumerate(row):
                attr = attributes[r][c]
                pens = [self.palette[p & 0x7F] for p in (background, multi[0], multi[1], attr & 0x77)]
                glyph = bank[code * 8:code * 8 + 8]
                for y, byte in enumerate(glyph):
                    for x in range(8):
                        if attr & 8:
                            index = (byte >> (6 - 2 * (x // 2))) & 3
                        else:
                            index = 3 if byte & (0x80 >> x) else 0
                        out.putpixel((c * 8 + x, r * 8 + y), tuple(pens[index]))
        return out

    def alien(self, sheet, frame):
        f = sheet['fields']
        return self.render([[101, 102, 103]], self.bank(sheet, frame), f['alien_attribute'],
                           (f['multi_colour_1'], f['multi_colour_2']))

    def explosion(self, sheet, frame):
        f = sheet['fields']
        return self.render([[105, 106, 107]], self.bank(sheet, frame), f['alien_attribute'],
                           (f['multi_colour_1'], f['multi_colour_2']))


def alien_sheets(g, sheets):
    ordered = sorted(sheets, key=lambda s: s['play_order'])
    im = canvas('Aliens on all sixteen sheets',
                'Glyphs 101-103 per frame, sheet colours MULTI1/MULTI2/attribute, background black. '
                'Frames play 0, 1, 2, 1.', 120 + 8 * 112)
    for i, sheet in enumerate(ordered):
        col, row = i % 2, i // 2
        x, y = 40 + col * 580, 118 + row * 112
        f = sheet['fields']
        mode = 'multicolour' if f['alien_attribute'] & 8 else 'hires'
        label(im, (x, y), f"Sheet {sheet['play_order']:2}  (table {sheet['table_index']:X}, "
                          f"{f['alien_count']} aliens, {mode})", 16)
        for frame in range(3):
            im.paste(enlarged(g.alien(sheet, frame), 5), (x + frame * 135, y + 26))
        label(im, (x + 410, y + 34), f"attr ${f['alien_attribute']:02X}", 15, MUTED)
        label(im, (x + 410, y + 56), f"M1 ${f['multi_colour_1']:02X} M2 ${f['multi_colour_2']:02X}", 15, MUTED)
    return im


def formations(g, sheets):
    ordered = sorted(sheets, key=lambda s: s['play_order'])
    scale, cell = 1, 8
    im = canvas('Sheet formations and movement',
                'Initial X,Y from each sheet table on the 32-column play field; '
                'the blue trace is one pass of the movement pattern from the first alien.',
                120 + 4 * 262)
    for i, sheet in enumerate(ordered):
        col, row = i % 4, i // 4
        x0, y0 = 40 + col * 284, 116 + row * 262
        field = Image.new('RGB', (32 * cell, 25 * cell), tuple(g.palette[0]))
        alien = g.alien(sheet, 0)
        for x, y, _ in sheet['initial_positions']['triples']:
            field.paste(alien, (x * cell, y * cell))
        im.paste(field, (x0, y0 + 26))
        d = ImageDraw.Draw(im)
        d.rectangle((x0, y0 + 26, x0 + 32 * cell, y0 + 26 + 25 * cell), outline=LINE)
        first = sheet['initial_positions']['triples'][0]
        px, py = first[0], first[1] & 0x7F
        segments, points = [], [(px, py)]
        xt, yt = g.tables['XTBL'], g.tables['YTBL']
        directions = sheet['movement']['directions']
        # MVEALL reads entry pointer+1 first and wraps the pointer at the pattern length.
        for step in range(len(directions)):
            direction = directions[(step + 1) % len(directions)]
            nx = px + xt[direction] - (256 if xt[direction] > 127 else 0)
            ny = py + yt[direction] - (256 if yt[direction] > 127 else 0)
            wrapped = False
            if nx == 0:
                nx, wrapped = 29, True      # off left: start at right
            if nx >= 30:
                nx, wrapped = 1, True       # off right: move to left
            if ny == 0:
                ny, wrapped = 23, True      # off top: move to bottom
            if ny >= 24:
                ny, wrapped = 1, True       # off bottom: move to top
            if wrapped:
                segments.append(points)
                points = []
            px, py = nx, ny
            points.append((px, py))
        segments.append(points)
        for segment in segments:
            if len(segment) > 1:
                d.line([(x0 + (p[0] + 1.5) * cell, y0 + 26 + (p[1] + 0.5) * cell) for p in segment],
                       fill='#38bdf8', width=2)
        steps = len(directions)
        label(im, (x0, y0), f"Sheet {sheet['play_order']}: {steps} step{'s' if steps != 1 else ''}", 15)
    return im


def player_and_effects(g, sheet1):
    im = canvas('Ship, laser, bombs, explosions, stars and gauge',
                'Decoded from FRAK! and the TABLES animation data; enlarged 5x. '
                'Colours are the game attribute bytes in the captured VICE palette.', 980)
    label(im, (40, 116), 'Ship: glyphs 80-86, attr $71', 17)
    ship = g.render(SHIP_ROWS, g.bank(), 0x71)
    im.paste(enlarged(ship, 6), (40, 146))
    label(im, (330, 116), 'Laser: glyph 92 (LACHAR), attr $76', 17)
    for frame in range(2):
        im.paste(enlarged(g.render([[92]], g.bank(frame=frame), 0x76), 6), (330 + frame * 70, 146))
    label(im, (720, 116), 'Alien bomb: glyph 104, FICHAR frames', 17)
    for frame in range(2):
        im.paste(enlarged(g.render([[104]], g.bank(frame=frame), 0x75), 6), (720 + frame * 70, 146))
    label(im, (40, 320), 'Explosion: glyphs 105-107 from EXPLAN, three frames (sheet 1 colours)', 17)
    for frame in range(3):
        im.paste(enlarged(g.explosion(sheet1, frame), 5), (40 + frame * 140, 350))
    label(im, (40, 430), 'Stars: glyphs 117-124 = STCHAR + (Y AND 7); STCOL attributes, sheet 1 '
                         'MULTI1/MULTI2', 17)
    stars = list(range(117, 125))
    multi = (sheet1['fields']['multi_colour_1'], sheet1['fields']['multi_colour_2'])
    for i, code in enumerate(stars):
        attr = g.tables['STCOL'][i & 3]
        im.paste(enlarged(g.render([[code]], g.bank(), attr, multi), 6), (40 + i * 66, 460))
        label(im, (40 + i * 66, 516), str(code), 14, MUTED)
    label(im, (40, 560), 'Laser temperature gauge: frame 87/88, partial 93-99, full 100 (HEAT/8)', 17)
    gacoul = g.tables['GACOUL']
    for i, heat in enumerate((0, 20, 45, 70, 87)):
        rows, attrs = [], []
        for level in range(12):
            filled = heat // 8
            top = 11 - filled
            if level > top:
                code = 100
            elif level == top and heat & 7:
                code = 92 + (heat & 7)
            else:
                code = 32
            rows.append([87, code, 88])
            attrs.append([gacoul[11 - level], 0x71, 0x71])
        image = g.render(rows, g.bank(), attrs)
        im.paste(enlarged(image, 3), (60 + i * 220, 600))
        label(im, (60 + i * 220, 900), f'HEAT {heat}' + (' (over)' if heat >= 0x57 else ''), 15)
    return im


def title_letters(g, assets):
    letters = assets['title_letters']
    ttb = g.tables['TTB']
    cells = {}
    for i in range(0, len(ttb) - 4, 4):
        if ttb[i] == 0xFF:
            break
        x0, y0 = ttb[i], ttb[i + 1]
        address = ttb[i + 2] | ttb[i + 3] << 8
        name = next(k for k, v in letters.items() if v['address'] == address)
        for dx, dy in letters[name]['points']:
            x, y = x0 + dx, y0 + dy
            bit = g.tables['PLOXEL'][(y & 1) * 2 + (x & 1)]
            cells[(x // 2, y // 2)] = cells.get((x // 2, y // 2), 0x40) | bit
    rows = [[cells.get((c, r), 32) for c in range(40)] for r in range(7)]
    image = g.render(rows, g.bank(), 0x71)
    im = canvas('Title lettering from TTB',
                'Each point lights one quarter of a cell; FUNKIT ORs PLOXEL bits into glyphs $40-$4F. '
                'TITCOL changes every pass.', 380)
    im.paste(enlarged(image, 3), (40, 120))
    label(im, (40, 300), 'Letters: X A R G O N  W A R S from XDATA, ADATA, RDATA, GDATA, ODATA, '
                         'NDATA, WDATA, SDATA (80 x 50 plot grid).', 16, MUTED)
    return im


def screen_composition(g, screenshot, origin):
    shot = Image.open(screenshot).convert('RGB')
    scale = 2
    im = canvas('How the gameplay screen is built',
                'Verified VICE capture after 100 main-loop passes, with the character-cell regions '
                'the source draws (text window origin from the palette capture).', 120 + shot.height * scale + 40)
    im.paste(enlarged(shot, scale), (40, 116))
    d = ImageDraw.Draw(im)
    ox, oy = 40 + origin[0] * scale, 116 + origin[1] * scale

    def box(c0, r0, c1, r1, text, colour, dy=0):
        d.rectangle((ox + c0 * 16, oy + r0 * 16, ox + (c1 + 1) * 16 - 1, oy + (r1 + 1) * 16 - 1),
                    outline=colour, width=3)
        label(im, (40 + shot.width * scale + 20, 140 + dy), text, 16, colour)

    box(1, 1, 31, 23, 'Play field: aliens, bombs, stars, laser (cols 1-31)', '#f59e0b', 0)
    box(15, 21, 17, 23, 'Ship: SHIP pointer, 7 glyphs (rows 21-23)', '#22c55e', 40)
    box(34, 1, 38, 7, 'TEXT: score, rank, lives, sheet', '#38bdf8', 80)
    box(34, 8, 38, 21, 'Laser temperature gauge (PRTGAG)', '#ef4444', 120)
    box(34, 22, 38, 23, 'LASER / TEMP labels', '#a855f7', 160)
    box(0, 0, 32, 24, 'PRBOX frames: play field and side panel', '#64748b', 200)
    return im


def gifs(g, sheet1, output):
    frames = [enlarged(Image.merge('RGB', g.alien(sheet1, f).split()), 8) for f in FRAME_ORDER]
    path = output / 'alien-animation.gif'
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=GIF_MS, loop=0, optimize=False)
    boom = [enlarged(g.explosion(sheet1, f), 8) for f in (0, 1, 2)]
    path2 = output / 'explosion-animation.gif'
    boom[0].save(path2, save_all=True, append_images=boom[1:], duration=GIF_MS, loop=0, optimize=False)
    return [path, path2]


def main(output):
    output.mkdir(parents=True, exist_ok=True)
    assets_path = ANALYSIS / 'asset-data.json'
    palette_path = output / 'ted-palette.json'
    screenshot = ROOT / 'docs/images/restored-gameplay.png'
    assets = json.loads(assets_path.read_text())
    palette_data = json.loads(palette_path.read_text())
    g = Graphics(assets, palette_data['rgb'])
    sheets = assets['sheets']
    sheet1 = next(s for s in sheets if s['play_order'] == 1)
    figures = {
        'alien-sheets.png': alien_sheets(g, sheets),
        'sheet-formations.png': formations(g, sheets),
        'ship-and-effects.png': player_and_effects(g, sheet1),
        'title-lettering.png': title_letters(g, assets),
        'screen-composition.png': screen_composition(g, screenshot, palette_data['window_origin']),
    }
    images = {}
    for name, image in figures.items():
        path = output / name
        image.save(path, optimize=False)
    for path in [output / n for n in figures] + gifs(g, sheet1, output):
        with Image.open(path) as image:
            size = list(image.size)
        images[path.name] = {'size': size, 'sha256': digest(path.read_bytes())}
    manifest = {
        'method': ('Original glyph bits and tables decoded with TED character rules; nearest-neighbour '
                   'enlargement; layout diagrams drawn on the verified screenshot.'),
        'inputs': {'asset-data.json': digest(assets_path.read_bytes()),
                   'ted-palette.json': digest(palette_path.read_bytes()),
                   'restored-gameplay.png': digest(screenshot.read_bytes())},
        'palette': palette_data['source'],
        'alien_frame_order': FRAME_ORDER, 'gif_frame_duration_ms': GIF_MS,
        'gif_timing': ('Illustration only. In the game ANICHR advances a frame every ANISPD timer-2 '
                       'interrupts (4 to 14 depending on the sheet).'),
        'images': images,
    }
    (output / 'graphics-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=ANALYSIS / 'graphics')
    main(parser.parse_args().output_dir.resolve())
