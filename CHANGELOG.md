# Changelog

All notable changes to the Xargon Wars C16 preservation project. Dates are DD-MM-YYYY.

---

## [1.0.0] 20-10-2026

Initial preservation checkpoint: the surviving Xargon Wars source reassembled for the Commodore 16 and Plus/4.

### Added

- Preserved inputs: `Recovered Source/` (the 2026 D64 image and extraction, the 1992 PC export and its PKZIP archive, and the running `xargon_wars.prg`) and `Original Artifacts/` (cassette inlay, instruction card, gameplay screenshot and source-disk photo). All of them are kept byte for byte.
- `scripts/restore_c16.py`, the build pipeline. It reads the D64 directly, checks all 77 files against the 2026 extraction and cross-checks the 1992 export and ZIP. It expands the `.LIB` order from `ULTRA` (51 modules), assembles with ca65 and ld65, and adds the disk files `MUSIC/CODE` (`$1C00`) and `FRAK!` (`$3C00`).
- Verified output: all 10,747 bytes of the original `OBJ` listing match with zero differences, including the zero-page and page-3 variable values. The PRG is 12,274 bytes, loads at `$1010`, starts at `$1C80` and has SHA-256 `6b766dcd2c6abbcd47e29ed005d72c0f1c28dc1f95aa1186c11ffe972a1e5daf`.
- `scripts/compare_reference.py`, which explains the running PRG. Two edits in `ALIENS` reproduce its code, and the 21 bytes still different are all written by the program at run time. It also reports the leftover bytes after the code and two differing glyphs.
- `scripts/d64_image.py` (disk reader), `scripts/source_converter.py` (MOS assembler to ca65, including macros and repeated equates) and `config/c16.cfg` / `config/saver.cfg`.
- PlatformIO `c16` and `c16_debug` environments (pinned to `platformio/native@1.2.1`) that produce identical game bytes, plus a `Makefile`, `build.sh`, and VS Code tasks, settings and recommended extensions.
- `scripts/run_vice.py`, which launches the rebuild at `$1C80`, or the original through VICE autostart with `--original`.
- `scripts/verify_vice.py`, an automated VICE 3.10 check on a 16 KB PAL C16. It covers the title loop, scripted PLAY GAME selection at the original joystick test, the main loop and the running PRG's title loop.
- `scripts/publish_evidence.py`, which copies the checked reports and screenshots into `docs/`.
- `test/test_restoration.py`: 11 regression tests.
- GitHub Actions workflow: build, running-version comparison, tests, both PlatformIO environments and an output agreement check.
- Documentation: `README.md`, `QUICKSTART.md`, `TESTING.md`, `RIGHTS.md`, `src/README.md`, and in `docs/` the Artifacts, Build and Run, History and Credits, Sharing on GitHub, Source and Validation and Source Inventory guides, with the verification evidence and screenshots.
- Repository housekeeping: `.gitignore`, `.gitattributes` (no text, whitespace or diff handling for either preserved folder), `.editorconfig` and a concise `CLAUDE.md`.

### Known limits

- The default build is the source revision recorded in `OBJ`. The running PRG lacks the `GIDO` high-byte mask and uses `AND #$7F` in `BUMP`. By my reading of the code, both give the same screen addresses, but I haven't probed that.
- Not yet tested: the host keyboard mapping, a physical joystick, sound, scoring over a full game, sheet transitions, death and game over, high-score entry, a full play-through and real C16 or Plus/4 hardware.
