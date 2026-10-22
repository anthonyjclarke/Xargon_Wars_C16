# Quick Start

## Build

Install Python 3.9+, cc65 and VICE. From the project folder:

```sh
./build.sh
python3 scripts/run_vice.py
```

The output is `build/xargon-wars.prg`. It loads at `$1010` and starts at `$1C80` (`SYS 7296`). Use the launcher, because the rebuilt PRG has no BASIC stub. To run my original copy of the game instead:

```sh
python3 scripts/run_vice.py --original
```

---

## PlatformIO and VS Code

Open this folder in VS Code, install the recommended PlatformIO extension and run the default build task. From a PlatformIO terminal:

```sh
pio run -e c16
pio run -e c16 -t upload
```

`pio run -e c16_debug` gives the same game bytes. Outputs land in `build/platformio/<environment>/`.

---

## Controls and Checks

Press `J` on the title screen for joystick or `K` for keyboard. The keys are `ESC` left, `1` right, `F3` up, `HELP` down and `F1` fire. Move the menu box and press fire to play, change ships or sound, or start the demo. I haven't checked these by hand yet.

```sh
make test
make verify
make run-original
```

See [Build and Run](docs/BUILD_AND_RUN.md) and [Testing](TESTING.md) for details.
