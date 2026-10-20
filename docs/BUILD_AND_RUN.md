# Build and Run

## Requirements

To build, you need Python 3.9 or later and cc65 (`ca65`, `ld65`). VICE (`xplus4`) runs the game and the emulator checks. The build uses only the Python standard library. The graphics renderer for the developer reference needs Pillow 10.1 or later, but the game build doesn't.

PlatformIO Core and VS Code are optional front ends. I've validated against PlatformIO Core 6.1.19, ca65/ld65 V2.18 and VICE 3.10, all recorded in [tool checks](verification/tool-checks.json). The PlatformIO native platform is pinned to `platformio/native@1.2.1`. It supplies the build framework only: the custom builder calls the 6502 assembler, never a host compiler.

On macOS:

```sh
brew install cc65 vice
python3 -m pip install platformio==6.1.19
```

If `pio` only exists inside the VS Code PlatformIO extension, use that extension's terminal. The scripts look for cc65 and VICE on `PATH`, then in `/opt/homebrew/bin` and `/usr/local/bin`. On Linux, install your distribution's cc65 and VICE packages.

---

## Direct Build

```sh
python3 scripts/restore_c16.py
```

`./build.sh` and `make` run the same pipeline. Use `--build-dir build/custom` to write somewhere else.

The build follows these steps:

1. It reads `Recovered Source/2026/XargonWars-C16-d64copy.d64` directly. It requires all 77 directory entries to match the 2026 extraction byte for byte and pass the extraction manifest's hashes.
2. It cross-checks the 1992 export. Every source text file must match after case and line-ending normalization, every binary must be identical, and the PKZIP directory's CRC-32 and size must agree with the extracted folder.
3. It expands `.LIB` includes from the root module `ULTRA` in their original order. That's 51 modules in all.
4. It translates the MOS assembler syntax into ca65 and assembles the fixed-origin layout in [config/c16.cfg](../config/c16.cfg).
5. It adds the two separately loaded disk files that the source names: the tune table `MUSIC/CODE` at `$1C00` and the character set `FRAK!` at `$3C00`.
6. It checks every record in the original `OBJ` listing against the assembled bytes, and only reports success if all of them match.

The rebuild never copies bytes from the running PRG.

### Output Files

| File                        | Content                                   |
|:----------------------------|:------------------------------------------|
| `xargon-wars.prg`           | Runnable PRG, `$1010–$3FFF`               |
| `xargon.s`                  | Generated ca65 source with source markers |
| `xargon.lst`                | Assembler listing with addresses          |
| `xargon.labels`             | VICE-format label file                    |
| `xargon.map`, `.dbg`        | Linker map and debug information          |
| `sheets.bin`, `code.bin`    | The two assembled file regions            |
| `zeropage.bin`, `page3.bin` | Initial variable images, checked only     |
| `recovery-manifest.json`    | Disk files, hashes, modules and assets    |
| `comparison.json`           | Object-listing check and output hash      |
| `disk/`                     | Byte-preserving copies of the disk files  |

`python3 scripts/compare_reference.py` (or `make compare`) adds `reference-comparison.json` and the `running-variant/` comparison build. `make verify` adds the VICE logs, memory captures and screenshots.

---

## PlatformIO

```sh
pio run -e c16
pio run -e c16_debug
pio run -e c16 -t upload
pio run -e c16 -t clean
```

The release and debug environments call the same Python pipeline and produce identical program bytes. Outputs land in `build/platformio/c16/` and `build/platformio/c16_debug/`. The upload target opens a 16 KB PAL C16 in VICE. It doesn't send anything to physical hardware. There's no source-level VS Code debug adapter, so debug with the VICE monitor and the generated labels and listing.

### VS Code Tasks

The default build task calls PlatformIO. The other tasks cover the debug build, clean, emulator upload, the direct Python build, launching the original, the regression tests, the running-version comparison and the VICE verification. The `.seq` disk files and generated `.s` files open in `ca65` mode from the recommended [ca65 extension](https://github.com/tlgkccampbell/code-ca65). Save-time whitespace cleanup is off, to protect the historical inputs.

### Makefile

| Target              | Action                                 |
|:--------------------|:---------------------------------------|
| `make`              | Direct build                           |
| `make run`          | Build, then launch the rebuild in VICE |
| `make run-original` | LOAD and RUN the supplied running PRG  |
| `make test`         | Regression tests                       |
| `make compare`      | Explain the running PRG differences    |
| `make verify`       | Comparison plus the VICE checks        |
| `make probes`       | Rule probes in VICE                    |
| `make docs`         | Build, analysis and HTML handbook      |
| `make docs-html`    | HTML handbook from current Markdown    |
| `make docs-watch`   | Regenerate the handbook on every edit  |
| `make docs-check`   | Fail if the handbook is stale          |
| `make test-docs`    | Documentation tests                    |
| `make clean`        | Remove `build/` and `.pio/`            |

---

## Running the Game

```sh
python3 scripts/run_vice.py
python3 scripts/run_vice.py build/platformio/c16/xargon-wars.prg
python3 scripts/run_vice.py --original
```

The rebuilt PRG loads at `$1010` and starts at `$1C80`. It begins with attack-wave tables, not BASIC text, so BASIC `RUN` won't work. The launcher waits for the reset to finish, then uses the monitor to load the file at its saved address and jump to the entry point.

The supplied running PRG is a one-line BASIC program, `1 SYS7296`, followed by the game's memory from `$1010` to `$3FFE`. `--original` hands it to VICE autostart, which LOADs and RUNs it just as a user would. Neither launcher changes the original file.

The source also has `SAVER`, the routine that wrote the original cassette auto-run loader. That isn't part of this build. See the [Source Inventory](SOURCE_INVENTORY.md).

### Controls

`KEY-SCAN` maps `ESC`, `1`, `F3`, `HELP` and `F1` to left, right, up, down and fire. `JO/KE SELECTION` reads `J` for joystick and `K` for keyboard on the title page. The joystick routine tries port 0, then port 1. The menu box moves with up and down, and fire picks PLAY GAME, SHIPS (1–4), SOUND (on or off) or DEMO MODE. The game starts on keyboard control with three ships and sound on.

I took these mappings from the source, and the cassette instruction card agrees with them. The automated check sets the original joystick result flags directly, so it never exercises the host keyboard, sound or a physical joystick.

---

## Cleaning and Development

`make clean` removes `build/` and `.pio/` and leaves the original source, artwork and documentation alone.

The historical inputs are the build's source of truth. Read `build/xargon.s` to see the expanded assembly, but don't edit it: any change there is lost on the next build. A deliberate source change will also fail the strict object-listing check. Keep experiments on a separate branch, and see the [Porting Guide](PORTING_GUIDE.md#protect-the-preservation-build) for how to add a derivative build without disturbing this one.
