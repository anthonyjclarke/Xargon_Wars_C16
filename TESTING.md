# Testing

## Regression Tests

```sh
python3 -m unittest discover -s test -p 'test_*.py' -v
```

The tests need Python 3.9+ and cc65. They build in a temporary directory, so the normal output and the preserved inputs are left alone. All eleven pass at the 20 October 2026 checkpoint. The tests check:

- the complete PRG's hash, load address and length;
- every one of the 10,747 bytes in `OBJ`, and the exact set of addresses it covers;
- that the D64 is the only source, that the 1992 export and its ZIP agree with it, and which modules are unused;
- that the alternative roots `LISTER` and `ASSEM-SHEETS` assemble to the same bytes as `ULTRA`;
- that `SAVER` matches its listing `OBJ.ANT` except for the one known operand;
- the provenance of `FRAK!` and `MUSIC/CODE`;
- that two documented edits plus runtime-written state explain the running PRG;
- that input hashes are unchanged;
- historical syntax conversion;
- that missing, ambiguous or recursive includes, malformed hex records and cyclic disk chains are rejected.

The PRG hash is a deliberate preservation check. If it fails after a change you meant to make, the output no longer reproduces this source revision. Don't update the baseline until you've reviewed the byte differences.

---

## PlatformIO Agreement

```sh
./build.sh
pio run -e c16 -e c16_debug
cmp build/xargon-wars.prg build/platformio/c16/xargon-wars.prg
cmp build/xargon-wars.prg build/platformio/c16_debug/xargon-wars.prg
```

The direct, release and debug builds must all produce this SHA-256:

```text
6b766dcd2c6abbcd47e29ed005d72c0f1c28dc1f95aa1186c11ffe972a1e5daf
```

All three matched at the recorded checkpoint. The GitHub Actions workflow installs cc65 and PlatformIO, runs the build, the running-version comparison and the regression tests, builds both environments and compares their bytes. The VICE checks need a graphical desktop, so they run locally and aren't part of the workflow.

---

## Running-Version Comparison

```sh
python3 scripts/compare_reference.py
```

Both the rebuild and the running PRG are uncompressed saved-address images, so the script compares their memory directly, region by region. It then reassembles the source with the edits listed in `RUNNING_REVISION_EDITS` into `build/running-variant/`. Every remaining code difference must be a location that the program writes with a store or read-modify-write instruction, and the script names the instruction for each one. The result goes to `build/reference-comparison.json`. The `running-variant` build exists only for this comparison. It isn't a supported build target.

---

## VICE Verification

```sh
make verify
python3 scripts/verify_vice.py --build-dir build/platformio/c16
```

The script needs VICE with PNG screenshot support and a graphical desktop. It starts a fresh PAL C16 with 16 KB RAM, sound off, a cycle limit and a process timeout. It deliberately doesn't use warp mode: VICE skips drawing frames in warp, and the screenshots then showed stale, half-drawn screens.

The gameplay check works like this:

1. Load the rebuild and stop at `PARTY`, the title loop. Screenshot.
2. Set `YBOX` to 0 so the box is on PLAY GAME.
3. Stop inside `MVEBOX` just after its `JSR REDJOS` joystick read. Set the result flags `JMOVE = 1`, `JUP = JDOWN = 0` and `JFIRE = $80`, then resume.
4. The original code runs `WHJUMP`, `STGME` and `PLGAME`. Stop at the main loop `START`, screenshot, let it run 100 more passes, screenshot again and save memory.
5. Require `PLAYIN = 1`, `DEMO = 0`, `GLIVES = 3`, `SHEETN = 0` and `FINITO = 0`.

No instruction is patched, and nothing jumps past the original control flow.

The reference check autostarts the running PRG. VICE LOADs it from a virtual disk and RUNs its `SYS 7296`. The check stops at that version's title loop, `$310C`, and saves memory. Of the 21 bytes that differ only because of runtime state, 19 already hold the snapshot's values at that point. The other two are the title's random delay operand and its cycling colour, which change on every pass.

On one run during development, the reference step exited with an error after reaching its breakpoint. A VICE window I'd launched by hand was still closing at the time. The next three runs passed. If it happens to you, close any other VICE windows and run it again.

The screenshot of the first `START` pass still shows "GO FOR IT !". VICE captures the last completed frame, and `NICSTR` clears the message just before the loop begins. The screenshot after 100 more passes shows play in progress. I've checked all the screenshots by eye. The rebuild's captures are the same on every run. The running PRG's title capture isn't: autostart timing varies, so the cycling title colour changes from run to run, and `publish_evidence.py` will show the file as changed even when nothing is wrong.

---

## Rule Probes and Analysis

```sh
make probes
python3 scripts/analyze_codebase.py
```

The probe script uses VICE. It calls original routines from a small caller at `$1B80`, in memory that nothing else uses, with interrupts off and controlled RAM, and saves memory afterwards. It also observes the running game at breakpoints. It covers seven things:

- points per sheet and level;
- the extra life around 1,000;
- score overflow;
- `LEVINC`;
- the Y register at `CHSEL`'s keyboard test;
- the raster and timer-2 periods;
- the main-loop period.

The results go to `build/rule-probes/`. The reviewed copy is [docs/analysis/rule-probes.json](docs/analysis/rule-probes.json). No game instruction is changed. These are focused observations, not a play-through.

The analysis script checks that the listing accounts for every assembled byte before it writes the [generated references](docs/analysis/README.md).

---

## Documentation Tests

```sh
make docs-check
make test-docs
```

These need Node.js 20 or later. They check that the saved [HTML handbook](docs/XARGON_WARS.html) matches its inputs. They also test link rewriting, embedded images and diagrams, failure on broken links, escaping, determinism and watch mode. See [Maintaining the HTML Documentation](docs/HTML_DOCUMENTATION.md).

---

## Verification Limits

The automated checks show that the source assembles, that the object listing matches, that the running version's differences are accounted for, that the title renders and that gameplay starts. I haven't tested host-key mapping, joystick compatibility, audible sound, scoring over a whole game, wave transitions, death and game over, high-score entry, a full play-through or real hardware.

The controls and menu behaviour in these guides come from the source and the instruction card. When I add manual-test results, I'll keep them separate from the scripted evidence and record the machine model, emulator version, input method and game revision.
