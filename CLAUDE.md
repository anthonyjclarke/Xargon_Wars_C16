# Xargon Wars C16 – Claude Context

## Target

Commodore 16 / Plus/4, PAL, 16 KB RAM, MOS 7501 (6502 instruction set), TED video and sound. The project reassembles the 1985 source for the preservation build (v1.0.0) with ca65/ld65. It is not an ESP32 project: the global CYD/TFT rules don't apply.

## Build facts

- One pipeline: `scripts/restore_c16.py`. `build.sh`, Make, PlatformIO (`c16`, `c16_debug`) and VS Code all call it, and all must produce identical bytes.
- Source of truth: `Recovered Source/2026/XargonWars-C16-d64copy.d64`, read directly. The 1992 export is a cross-check only, never a fallback.
- Root module `ULTRA`. `.LIB NAME*` is a prefix match and `.LIB NAME` is exact. Exactly one match is required.
- PRG loads at `$1010` with no BASIC stub. Entry is `$1C80` (`SYS 7296`). `FRAK!` goes at `$3C00` and `MUSIC/CODE` at `$1C00`, both from the disk.
- `OBJ` (MOS hex) must match all 10,747 bytes, zero page and page 3 included. The PRG SHA-256 baseline is in `test/test_restoration.py`.

## Never

- Modify, re-encode or tidy anything in `Recovered Source/` or `Original Artifacts/`. `.gitattributes` and `.editorconfig` protect them.
- Copy bytes from `Recovered Source/xargon_wars.prg` into the build. It's a post-run memory snapshot of a slightly different revision.
- Edit `build/` output by hand, or change the hash baseline without reviewing the byte differences.
- Use VICE warp mode for screenshot checks, because frames are skipped and the captures go stale.

## Gotchas

- `SHTABL` is defined twice (label and equate). The converter turns the repeat into `.assert`.
- The running revision differs only at `ALIENS:150–152` and `ALIENS:227`. See `RUNNING_REVISION_EDITS` in `scripts/compare_reference.py`.
- VICE monitor numbers are hex (`ignore 1 64` means 100 hits). After `delete`, checkpoint numbers restart at 1.
- `PLGAME` is entered from inside the menu IRQ handler (`SLOB` → `MVEBOX` → `WHJUMP`) and never returns with `RTI`.
- `CHSEL` passes the keyboard row in `X`, but `KEYIT` reads `Y`.
- `CFLAG` = 1 means sound ON, even though one source comment says otherwise.
