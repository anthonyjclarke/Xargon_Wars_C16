"""Regression checks for historical syntax, provenance and assembled bytes."""

import contextlib
import hashlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from compare_reference import compare
from d64_image import D64Image
from restore_c16 import ROOT, IMAGE, assemble, build_game, mos_hex, prepare_sources
from source_converter import convert, flatten

PRG_SHA256 = '6b766dcd2c6abbcd47e29ed005d72c0f1c28dc1f95aa1186c11ffe972a1e5daf'


class RestorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='xargon-test-')
        cls.build = Path(cls.temp.name)
        cls.before = {p: hashlib.sha256(p.read_bytes()).hexdigest()
                      for folder in ('Recovered Source', 'Original Artifacts')
                      for p in (ROOT / folder).rglob('*') if p.is_file() and p.name != '.DS_Store'}
        with contextlib.redirect_stdout(io.StringIO()):
            cls.output = build_game(cls.build).read_bytes()
            cls.comparison = compare(cls.build)
        cls.manifest = json.loads((cls.build / 'recovery-manifest.json').read_text())
        cls.sources, cls.disk, _ = prepare_sources(cls.build / 'inputs')

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def byte(self, address):
        return self.output[2 + address - 0x1010]

    def test_complete_prg_matches_verified_baseline(self):
        self.assertEqual(len(self.output), 12274)
        self.assertEqual(self.output[:2], b'\x10\x10')
        self.assertEqual(hashlib.sha256(self.output).hexdigest(), PRG_SHA256)

    def test_every_object_record_matches(self):
        obj = mos_hex(self.sources['OBJ'])
        self.assertEqual(len(obj), 10747)
        for address, value in obj.items():
            if address >= 0x1000:
                self.assertEqual(self.byte(address), value, hex(address))
        low = (self.build / 'zeropage.bin').read_bytes() + (self.build / 'page3.bin').read_bytes()
        self.assertEqual(bytes(obj[a] for a in sorted(obj) if a < 0x1000), low)
        covered = set(range(0x0002, 0x002E)) | set(range(0x033C, 0x03B3)) | \
            set(range(0x1010, 0x1B02)) | set(range(0x1C80, 0x3AE6))
        self.assertEqual(set(obj), covered)

    def test_disk_is_the_only_source_and_1992_export_agrees(self):
        self.assertEqual(self.manifest['disk_files'], 77)
        check = self.manifest['older_export_cross_check']
        self.assertTrue(check['zip_matches_folder'])
        self.assertFalse([f for f in check['files'] if f['status'] == 'different'])
        self.assertIn('ULTRA', self.manifest['used_modules'])
        for name in ('HAK/SCREEN', 'HEXER', 'MUFF', 'CHARS', 'LISTER', 'ASSEM-SHEETS', 'SAVER'):
            self.assertIn(name, self.manifest['unused_sources'])
        self.assertIn('SOURCE: SHIP:1', (self.build / 'xargon.s').read_text())

    def test_alternate_roots_assemble_the_same_bytes(self):
        lister = self.build / 'lister'
        lister.mkdir()
        assemble(lister, self.sources, 'LISTER', 'xargon', ROOT / 'config/c16.cfg')
        for name in ('sheets.bin', 'code.bin'):
            self.assertEqual((lister / name).read_bytes(), (self.build / name).read_bytes())
        sheets = self.build / 'assem-sheets'
        sheets.mkdir()
        assemble(sheets, self.sources, 'ASSEM-SHEETS', 'xargon', ROOT / 'config/c16.cfg')
        self.assertEqual((sheets / 'sheets.bin').read_bytes(), (self.build / 'sheets.bin').read_bytes())

    def test_saver_matches_its_listing_except_one_operand(self):
        saver = self.build / 'saver'
        saver.mkdir()
        assemble(saver, self.sources, 'SAVER', 'saver', ROOT / 'config/saver.cfg')
        code = (saver / 'saver.bin').read_bytes()
        listing = mos_hex(self.sources['OBJ.ANT'])
        self.assertEqual(len(listing), len(code))
        changed = {a: (code[a - 0x3000], v) for a, v in listing.items() if code[a - 0x3000] != v}
        # LDX #<END: the source has END = $0326, the listing was made with $0324.
        self.assertEqual(changed, {0x3037: (0x26, 0x24)})

    def test_separately_loaded_assets_have_disk_provenance(self):
        frak = self.disk['FRAK!'].data
        music = self.disk['MUSIC/CODE'].data
        self.assertEqual(frak[:2], b'\x00\x3c')
        self.assertEqual(self.output[2 + 0x3C00 - 0x1010:], frak[2:])
        self.assertEqual(music[:2], b'\x00\x1c')
        self.assertEqual(self.output[2 + 0x1C00 - 0x1010:2 + 0x1C80 - 0x1010], music[2:])
        # GLOPPY (MUSIC) carries the same tune bytes saved at $1E80.
        self.assertEqual(self.disk['GLOPPY (MUSIC)'].data[2:], music[2:])

    def test_running_prg_is_explained(self):
        report = self.comparison
        self.assertTrue(report['running_revision_reproduced'])
        self.assertEqual(report['unexplained_code_differences'], [])
        self.assertEqual([(e['module'], e['line']) for e in report['running_revision_edits']],
                         [('ALIENS', 150), ('ALIENS', 151), ('ALIENS', 152), ('ALIENS', 227)])
        self.assertEqual(report['running_code_end'], '$3ADF')
        self.assertEqual(report['character_set_differences']['glyphs'], [125, 126])
        self.assertEqual({r['region']: r['differences'] for r in report['regions']}['Sheet tables'], 0)

    def test_inputs_are_unchanged_by_build(self):
        after = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.before}
        self.assertEqual(self.before, after)

    def test_missing_ambiguous_and_recursive_includes_fail(self):
        with self.assertRaisesRegex(ValueError, 'ambiguous/missing'):
            flatten({'MAIN': ['.LIB LOST*']}, 'MAIN')
        with self.assertRaisesRegex(ValueError, 'ambiguous/missing'):
            flatten({'MAIN': ['.LIB AL*'], 'ALPHA': [], 'ALTO': []}, 'MAIN')
        with self.assertRaisesRegex(ValueError, 'ambiguous/missing'):
            flatten({'MAIN': ['.LIB SHEET1'], 'SHEET10': []}, 'MAIN')
        with self.assertRaisesRegex(ValueError, 'Recursive'):
            flatten({'MAIN': ['.LIB MAIN*']}, 'MAIN')

    def test_historical_syntax_keeps_instructions_and_literals(self):
        result = convert([('TEST', 1, '.MAC SAVE'), ('TEST', 2, 'PHA'), ('TEST', 3, '.MND'),
                          ('TEST', 4, 'SELFMD LDA $FFFF,X'),
                          ('TEST', 5, 'REG = $FF00'),
                          ('TEST', 6, "TEXT .BYTE 'A;B',0"),
                          ('TEST', 7, "LDA #'Z"),
                          ('TEST', 8, 'SAVE'),
                          ('TEST', 9, 'SELFMD = $1234'),
                          ('TEST', 10, 'BUF *=*+32')])
        self.assertIn('.macro SAVE', result)
        self.assertIn('.endmacro', result)
        self.assertIn('SELFMD: LDA $FFFF,X', result)
        self.assertIn('REG = $FF00', result)
        self.assertIn('TEXT: .BYTE "A;B",0', result)
        self.assertIn("LDA #'Z'", result)
        self.assertIn('\nSAVE\n', result)
        self.assertIn('.assert SELFMD = $1234, error', result)
        self.assertIn('BUF: .res 32', result)

    def test_invalid_hex_and_cyclic_disk_fail(self):
        with self.assertRaisesRegex(ValueError, 'checksum'):
            mos_hex([';011800000000'])
        disk = D64Image(IMAGE)
        data = bytearray(disk.data)
        # Isolated synthetic cycle on the first sector; no original file edits.
        data[0:2] = b'\x01\x00'
        disk.data = data
        with self.assertRaisesRegex(ValueError, 'Cyclic'):
            list(disk.chain(1, 0))


if __name__ == '__main__':
    unittest.main()
