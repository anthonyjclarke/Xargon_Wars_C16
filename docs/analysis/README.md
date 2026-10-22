# Generated Developer References

## Contents

| File                                       | Content                                  |
|:-------------------------------------------|:-----------------------------------------|
| [CODE_REFERENCE.md](CODE_REFERENCE.md)     | Modules, variables, write sites, symbols |
| [codebase-index.json](codebase-index.json) | The same catalogue plus transfers        |
| [asset-data.json](asset-data.json)         | Font, tune, sheets and named tables      |
| [font-hires.svg](font-hires.svg)           | `FRAK!` glyphs, one bit per pixel        |
| [font-multicolor.svg](font-multicolor.svg) | `FRAK!` glyphs, two bits per pixel       |
| [alien-glyphs.svg](alien-glyphs.svg)       | All 16 sheets' alien glyph data          |
| `graphics/`                                | Figures, GIFs, palette and manifest      |

The reviewed [rule-probes.json](../verification/rule-probes.json), seven controlled VICE observations, sits with the other evidence in `docs/verification/`.

The [codebase analysis](../../CODEBASE_ANALYSIS.md) explains and illustrates all of this. The SVG atlases use neutral index colours. The figures in `graphics/` use the TED palette captured from VICE.

---

## Codebase Index Fields

- `assembly_order` lists the 51 modules in `.LIB` order.
- `modules` gives each disk source file's extracted copy, byte count and hash, its logical and instruction line counts, the PRG bytes allocated to it, and its position in the assembly.
- `symbols` lists every definition in the assembled modules: defining module and line, address, kind, comment, the expression for equates, and `span_to_next_symbol`.
- `variables` lists the zero-page, page-3 and `EXTRA-MEMORY` allocations with their sizes.
- `direct_transfers` lists every JSR, JMP and branch with its operand text, resolved target address and target module.
- `notable_writes` lists every write instruction whose target falls in the code, the character set, screen or colour RAM, or the TED registers, with a category.
- `byte_owner_ranges` maps every PRG byte to the disk module and line that produced it.
- `unreferenced_symbols` lists symbols that no operand names.

Addresses are JSON integers. `span_to_next_symbol` is layout, not a declared size. A symbol's `kind` is a conservative guess: `instruction-label` means the next statement is an instruction, which may be a branch target rather than a routine. Direct transfers don't include fall-through, interrupt vectors, the `WHJUMP` computed branch or patched operands, so the list isn't a call graph.

---

## Asset Data Fields

- `font` is the 1,024 bytes of `FRAK!` from `$3C00`, as loaded. The game later rewrites some glyphs.
- `tune` is the 128-byte table at `$1C00`. Each note is three bytes: frequency low, frequency high and length, with `$FF` ending a tune.
- `sheets` has one record per `SHTABLE` entry. Each gives the play order, the 16 decoded fields and raw entry bytes, the movement directions, the initial position triples and the 72-byte alien glyph block.
- `tables` maps original symbol names to address, length and hex bytes. Lengths are taken from the source declarations.
- `title_letters` gives the decoded point lists for each big title letter.
- `runtime_glyph_addresses` gives where `ANICHR`, the scroller and the death sequence write into the character set.

Colours are TED attribute bytes, `(luminance << 4) | colour`. Decode bytes explicitly, and remember that `.WORD` tables are little-endian.

---

## Reproduction

```sh
./build.sh
python3 scripts/analyze_codebase.py
```

The analysis uses only the Python standard library and the build outputs. Before writing anything, it checks that the listing ownership covers every assembled byte exactly. The same inputs always produce the same output.

The figures, palette and probes need extra tools:

```sh
python3 scripts/capture_palette.py
python3 scripts/render_game_graphics.py
python3 scripts/probe_gameplay_rules.py
cp build/rule-probes/rule-probes.json docs/verification/
```

`capture_palette.py` and `probe_gameplay_rules.py` need VICE and a graphical desktop. `render_game_graphics.py` needs Pillow 10.1 or later. [graphics-manifest.json](graphics/graphics-manifest.json) records the SHA-256 of the renderer's three inputs and of every image it writes. The GIF frame time (160 ms) is for illustration only. The probes and the palette are reviewed snapshots: rerun them only when you mean to, and review the results before copying them in.
