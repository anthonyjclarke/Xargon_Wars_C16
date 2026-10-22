# Source Inventory

## Preserved Collections

| Path                                    | Content                                |
|:----------------------------------------|:---------------------------------------|
| `Original Source Recovered/2026/*.d64`           | 2026 capture of my source disk         |
| `Original Source Recovered/2026/XargonWars-C16/` | Extraction, `manifest.json`, c1541 log |
| `Original Source Recovered/1992/DISK7A/`         | 1992 PC export, 77 files plus `INDEX`  |
| `Original Source Recovered/1992/*.ZIP`           | Original PKZIP 1.0 archive of `DISK7A` |
| `Original Artifacts/xargon_wars.prg`      | Running game, `1 SYS7296` single file  |
| `Original Artifacts/`                   | Inlay, card, screenshot, disk photo    |

The disk image is 175,531 bytes: a 35-track D64 with an error map, and the map flags no sectors. Its SHA-256 is `5d400d85…5588cd`, and it matches the `source_sha256` recorded in the extraction manifest. The disk header reads `PEUGEOT 205 GTI`, ID `85`. The directory holds 77 files and shows 11 blocks free.

`DISK7A - Xargon Wars C16.ZIP` is also published as `DISK7A.ZIP` in Mark Hardisty's Gremlin Graphics Archive, with the same CRC-32 and size, and its 78 files match the archive's `DISK7A/` folder ([Gremlin Archive and the Book](GREMLIN_ARCHIVE.md#in-this-project)).

The 1992 export uses shortened PC filenames, lower-case text and CRLF line endings. Its `INDEX` file maps each PC name back to the Commodore filename, with block counts and export times. The build reads `INDEX` and compares every file with its disk counterpart. Text files match after case and line-ending normalization, and binary `.BIN` files are identical. The `.BAS` files are detokenized listings, so they can't be compared byte for byte, but they're readable.

`.DS_Store` files are macOS metadata. The build and the hash checks ignore them, and Git doesn't track them.

---

## Build Inputs

The root module is `ULTRA`. Its `.LIB` lines pull in 50 more modules, in this order:

1. `VARS` and `EXTRA-MEMORY`: zero page, page 3, `$0400` and `$0560`.
2. `SHTABLE` and `SHEET1`–`SHEETG`: the 16 sheets at `$1010`.
3. The start-up code in `ULTRA` at `$1C80`, then `MACROS` and `MAIN-VARS`.
4. `SCROLL-BUFFER`, `RANK-MASTER`, `STARTER`, `GAME-OVER`, `SCORE-ROUTINES`, `TABLES`, `UTILS`, `SETUP` and `SCREEN`.
5. `STARS`, `PLAY-GAME`, `IRQ`, `SHIP`, `GAUGE`, `SOUND`, `SETSHEET`, `ALIENS`, `ANIMATE`, `KILLER` and `BOMBS`.
6. `JOYSTIK`, `MAGNIFICENT`, `TITLE-WORKS`, `HIGH-STUFF`, `DEATH-MARCH`, `SMOOTH-SCROLL`, `TUNE`, `KEY-SCAN` and `JO/KE SELECTION`.

A `.LIB` name ending in `*` is a prefix match, so `MAIN-VA*` finds `MAIN-VARS`, and a name without `*` must match exactly. Every reference has to resolve to exactly one disk file. `ULTRA` comments out `HEXER`, `HAK/SCREEN`, `MUFF` and `CHARS`, and the build keeps them out.

Two separately loaded disk files complete the game:

| Disk file    | Load    | Bytes | Why it's needed                 |
|:-------------|:--------|:------|:--------------------------------|
| `MUSIC/CODE` | `$1C00` | 128   | `MAIN-VARS` sets `TUNDAT=$1C00` |
| `FRAK!`      | `$3C00` | 1,024 | `ULTRA`: "JUST LOAD ON 'FRAK!'" |

---

## Other Source Files

| File           | What it is                                    |
|:---------------|:----------------------------------------------|
| `OBJ`          | Game object listing (MOS hex), 10,747 bytes   |
| `LISTER`       | Copy of `ULTRA` with `.OPT NOL` commented out |
| `ASSEM-SHEETS` | Root for `SHTABLE` and the sheets only        |
| `SAVER`        | Saves the cassette auto-run loader, `$3000`   |
| `OBJ.ANT`      | MOS hex listing of `SAVER`, 192 bytes         |
| `HAK/SCREEN`   | Commented-out cheat: keys 0–F pick a sheet    |
| `HEXER`        | Commented-out "HEX CONVERTOR" routine         |
| `MUFF`         | Commented-out ship glyphs at `$3E80`          |
| `CHARS`        | Commented-out glyph source at `$3E00`         |

`LISTER` and `ASSEM-SHEETS` assemble to exactly the same bytes as `ULTRA`, and the tests check this. `SAVER` matches `OBJ.ANT` except for one operand: at `$3037`, `LDX #<END` is `$26` in the source and `$24` in the listing. The listing came from a revision that still had `END = $0324`.

---

## Binary Files on the Disk

| Disk file              | Load    | Identification                             |
|:-----------------------|:--------|:-------------------------------------------|
| `FRAK!`                | `$3C00` | Game character set (build input)           |
| `CAMEL (CHARS)`        | `$3C00` | Earlier set; 14 glyphs differ from `FRAK!` |
| `MEGA-SUPER`           | `$3C00` | Unrelated character set                    |
| `MUSIC/CODE`           | `$1C00` | Tune table (build input)                   |
| `GLOPPY (MUSIC)`       | `$1E80` | Same tune bytes saved at another address   |
| `@`                    | `$3200` | 1,536 bytes of unidentified data           |
| `SUPER-LOAD`           | `$1800` | C16 loader for `OBJ` hex files             |
| `TEST-B`               | `$1F00` | Test harness; calls don't match this build |
| `JINGLE1`, `JINGLE2`   | `$1001` | C16 BASIC sound experiments                |
| `MUSIC-MAKER`, `WASAL` | `$1001` | C16 BASIC tune makers                      |
| `BOOT ALL`             | `$0801` | C64 BASIC boot for `DOS5.2` and `EDITOR`   |
| `DOS5.2`               | `$CC00` | C64 DOS wedge, "(C)BUGGA-SOFT 1984"        |
| `EDITOR`               | `$C000` | "COMMODORE 64 EDITOR V072982"              |
| `HYPRA-LOAD OBJ`       | `$0801` | C64 fast-loader program                    |
| `ASM.C64`              | `$0801` | C64 assembler                              |

The C64 programs show that the disk was used on my C64 development machine. The source was assembled there, and the object code went to the C16. [Dorks Dilemma's History and Credits](https://github.com/anthonyjclarke/Dorks_Dilemma_C16/blob/main/docs/HISTORY_AND_CREDITS.md) describes that setup. I've identified these files from their load addresses, embedded text and the 1992 BASIC listings. Apart from `FRAK!` and `MUSIC/CODE`, none of them are used by the build.

---

## Running Version

`Original Artifacts/xargon_wars.prg` is 12,288 bytes. It loads at `$1001` and ends at `$3FFE`, and its SHA-256 is `835d26e3…69cec`. A BASIC line `1 SYS7296` starts it at `$1C80`. It isn't compressed. Its file date is 10 August 2014, and I don't know who made the single-file version. [Source and Validation](SOURCE_AND_VALIDATION.md) compares it in full.

The complete per-file record, including every hash and directory index, is generated as `build/recovery-manifest.json`. The checked copy is in [verification/source-manifest.json](verification/source-manifest.json).
