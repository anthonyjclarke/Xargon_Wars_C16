# Gremlin Archive and the Book

## About This Chapter

The first five sections are written to be reused unchanged in each of my Micro Projects C16 reconstructions (Xargon Wars, Xargon's Revenge, Dork's Dilemma, Tycoon Tex). Only [In This Project](#in-this-project) is specific to Xargon Wars. I checked the links and the archive contents on 22 October 2026.

---

## A Gremlin in the Works

*A Gremlin in the Works* by Mark Hardisty, published by [Bitmap Books](http://www.bitmapbooks.co.uk/products/a-gremlin-in-the-works), is the officially endorsed history of Gremlin Graphics, endorsed by founder Ian Stewart. The 572-page book follows the company from Monty Mole and Thing on a Spring to its purchase by Infogrames in 1999, with interviews, letters, photographs and design documents. Mark announced it on the archive in the post [A Gremlin in the Works – The Book](https://www.gremlinarchive.com/index.php/2016/05/22/a-gremlin-in-the-works-the-book/) (22 May 2016).

I contributed to the book and to the archive. Mark's post [A Gremlin in the Works – Anthony Clarke](https://www.gremlinarchive.com/index.php/2017/07/31/a-gremlin-in-the-works-anthony-clarke/) (31 July 2017) introduces my part. In 1985 I joined Gremlin with Jason Perkins and Mark Rogers as Micro Projects Limited. Micro Projects wrote many of Gremlin's C16 games, as well as Thing on a Spring on the C64 and its port of Monty on the Run. The book tells the Micro Projects story in full.

---

## The Gremlin Graphics Archive

[The Gremlin Graphics Archive](https://www.gremlinarchive.com/) is Mark Hardisty's companion site to the book. It collects Gremlin's games, box art, adverts, letters, royalty statements, staff photographs and source code. Posts relevant to Micro Projects include:

| Post                                             | Date         |
| :----------------------------------------------- | :----------- |
| [Micro Projects Source Code][ga-src]             | 25 May 2016  |
| [Micro Projects Royalty Statements][ga-roy]      | 24 May 2016  |
| [Compliment Slip / Royalty Notes][ga-slip]       | 24 May 2016  |
| [Early Tradeshow Leaflet][ga-trade]              | 23 May 2016  |
| [Anthony Clarke Photograph][ga-photo]            | 2 June 2016  |
| [A Gremlin in the Works – Anthony Clarke][ga-me] | 31 July 2017 |

Each game also has its own post: for example [Xargon's Revenge (C16/Plus4)][ga-xr] (1 November 2016) and [Xargon Wars – Trade Promotion][ga-xw] (24 May 2016). The compilations have theirs too: [C16 Classics][ga-classics] (13 February 2021) and [C16 Omnibus][ga-omnibus] (20 December 2021).

---

## My Development Disks in the Archive

The [Micro Projects Source Code][ga-src] post holds the Oric and C16 assembler source I donated for many of the company's games, including the unreleased Ultra. Its download, [Old-Development-Disks.zip][ga-zip] (1,894,396 bytes, 846 entries), is my 1992 PC export of the original Commodore disks, re-zipped in 2014. It has two folders, `Disk 1-6/` and `Disk 7-11/`. Each disk is there both as my 1992 PKZIP file (for example `DISK9.ZIP`) and as an extracted folder, with a `READ.ME` from 1992 that names them:

| Disk     | Contents (from `READ.ME`)      |
| :------- | :----------------------------- |
| `DISK1A` | Tycoon Tex C64                 |
| `DISK1B` | Dorks Dilemma C64              |
| `DISK2`  | Utilities                      |
| `DISK3`  | Thingy                         |
| `DISK4A` | Graphics Editor                |
| `DISK4B` | Graphic2                       |
| `DISK5`  | Dorks Dilemma C16              |
| `DISK6`  | Tycoon Tex C16                 |
| `DISK7A` | Xargon Wars C16                |
| `DISK7B` | Xargon Wars C16 (Hack Version) |
| `DISK8`  | Revenge of Xargon (Xargon II)  |
| `DISK9`  | Xargon's Revenge               |
| `DISK10` | Xargon's Revenge – 5 lives     |
| `DISK11` | `LOAD "*",8,1`                 |

Each disk ZIP includes an `INDEX` listing the original Commodore directory next to the PC file names. One thing to watch: in the extracted `Disk 7-11/DISK9/` folder, `LOADER.BIN` is 0 bytes, while `DISK9.ZIP` itself holds the full file. Compare against the disk ZIPs, not the extracted folders.

---

## Plus/4 World and the Archive

[Plus/4 World](https://plus4world.powweb.com/) has entries for these games. Its [Xargon's Revenge entry](https://plus4world.powweb.com/software/Xargons_Revenge) says the early-stages and disk versions were rebuilt from source files on disks I gave to Mark Hardisty, which are the 1992 export above. Check each game's entry for similar notes. Copies labelled "early stages", "disk version" or "with loading screen" are then not independent releases. They come from my own development disks, and only the original cassettes show what was actually sold.

---

## How to Cite

> Mark Hardisty, *A Gremlin in the Works*, Bitmap Books. Officially endorsed history of Gremlin Graphics.

> Mark Hardisty, "Micro Projects Source Code", The Gremlin Graphics Archive, 25 May 2016, <https://www.gremlinarchive.com/index.php/2016/05/25/micro-projects-source-code/>. Download: `Old-Development-Disks.zip`.

> Mark Hardisty, "A Gremlin in the Works – Anthony Clarke", The Gremlin Graphics Archive, 31 July 2017, <https://www.gremlinarchive.com/index.php/2017/07/31/a-gremlin-in-the-works-anthony-clarke/>.

---

## In This Project

The 1992 source in `Original Source Recovered/1992/` is the archive's `DISK7A`. `DISK7A - Xargon Wars C16.ZIP` has the same CRC-32 (`c543700d`) and size (88,351 bytes) as `Disk 7-11/DISK7A.ZIP` in the archive. All 78 extracted files in `Original Source Recovered/1992/DISK7A/` (77 plus `INDEX`) match the archive's `DISK7A/` folder by CRC-32 and size, so this disk doesn't have the empty-file problem noted above.

The ten machine-code programs in the 2026 extraction also match the archive's `DISK7A` `.BIN` files, which is expected because the 1992 `.BIN` files are identical to the disk. Some are on other disks too: `DOS5.2` is on nine, `EDITOR` on seven, and `SUPER-LOAD` and `MEGA-SUPER` on six. The D64 image, the extracted text and BASIC files, the running `xargon_wars.prg` and `Original Artifacts/` match nothing in the archive.

Two archive files bear on this game, and neither is in this project yet.

### `DISK7B`, the Hack Version

`DISK7B.ZIP` is 88,007 bytes with CRC-32 `6f7f05c3`, and its folder holds 79 files. 69 of them match `DISK7A`. `LISTER` is missing, `ANT` (an object listing in MOS hex) and `PAUSE` are new, and eight differ: `ALIENS`, `HAK/SCREEN`, `INDEX`, `IRQ`, `OBJ`, `PLAY-GAME`, `TITLE-WORKS` and `ULTRA`.

Its `ALIENS` has exactly the two edits that reproduce the running `xargon_wars.prg` (see [The Two Revisions](SOURCE_AND_VALIDATION.md#the-two-revisions)). Lines 150–152 (`LDA IH`, `AND #$F`, `STA IH`) are gone, and line 227 reads `AND #$7F` instead of `AND #$0F`. Nothing else in `ALIENS` changes apart from the header and blank comment lines.

The rest of `DISK7B` goes further. `ULTRA` adds `HACK`, `PAWS` and `PAWSFG` flags, includes `PAUSE` and the previously commented-out `HAK/SCR`, and names `UDG*` instead of `FRAK!` as the character set. `PAUSE` holds the game while a key is held (its comment says Shift), in joystick mode only. `HAK/SCREEN` gains a `HACKER` routine that flashes the border, which `TITLE-WORKS` calls. `PLAY-GAME` reads `TED+2` instead of `TED+4`, tests `HACK` and calls `PAUSE`. The running PRG matches the `DISK7A` source except for the two `ALIENS` edits and bytes the program writes while it runs, so it has `DISK7B`'s `ALIENS` and none of these other changes. That fits a copy made between the two disks.

### `DISK10/XARGONWA.BIN`

`DISK10` is the "XARGON GAMES" disk, filed in the `READ.ME` as "Xargon's Revenge – 5 lives". Beside the Xargon's Revenge files it holds `XARGON WARS-1C80`, exported as `XARGONWA.BIN` (12,290 bytes, CRC-32 `280a5e8c`). It loads at `$1000` and covers `$1000–$3FFF`, and `$1C80` in its name is the game's entry point.

I compared it as memory with this project's build, `build/xargon-wars.prg` (`$1010–$3FFF`). `$1000–$100F` is zero and lies before the build's load address. The remaining 12,272 bytes differ in 340, and every one has an explanation:

| Range                        | Bytes | `XARGONWA.BIN` has                 |
| :--------------------------- | ----: | :--------------------------------- |
| `$1B80–$1BFE`                |   127 | `$FF` in the unused gap            |
| `$3AE6–$3AFE`, `$3B80–$3BFE` |   152 | `$FF` after the code               |
| `$3F29–$3F3F`                |    22 | Glyphs 101–103: an alien frame     |
| `$1C92–$3772`                |    39 | Variables the game writes          |

The 39 variable bytes are all store targets in the source: `LIVES` (3), `CFLAG` (1, sound on), `SHEETN`, `DELAY+1`, the lives digit in `SCLVES`, `CLRMES`, the `SLFMD1`/`SLFMD2` pointers, `TITCOL`, the "ON" text in `CSOU`, `CHZ`, `ADD+1`, `BRAN+1`, one byte of `SCRBUF`, `STRIN` and two entries in the high-score table `HISTBL`. `ANICHR` copies the current alien frame into glyphs 101–103 at `ALCHAR` (`$3F28`).

So `XARGONWA.BIN` is the `DISK7A` revision that this project reassembles, saved after it had run. It isn't the running revision. Its sheet tables, tune and code match the build byte for byte, including `ALIENS` lines 150–152 and 227, and its variables sit at the source revision's addresses (`CHZ` at `$32A3`, where the running PRG has `$329D`). It also lacks the running PRG's leftover bytes after the code and its stray text in glyphs 125 and 126. It has the `FRAK!` bytes there, and `$3FFF` too.

### Archive Posts

The archive's own Xargon Wars post is [Xargon Wars – Trade Promotion][ga-xw] (24 May 2016). It shows the trade promotion for the game, which Mark describes as Micro Projects' first C16 game for Gremlin. The `DISK7A` and `DISK7B` source is in the [Micro Projects Source Code][ga-src] download.

[ga-src]: https://www.gremlinarchive.com/index.php/2016/05/25/micro-projects-source-code/
[ga-zip]: http://agremlinintheworks.co.uk/archive/wp-content/uploads/2016/05/Old-Development-Disks.zip
[ga-roy]: https://www.gremlinarchive.com/index.php/2016/05/24/micro-projects-royalty-statements/
[ga-slip]: https://www.gremlinarchive.com/index.php/2016/05/24/compliment-slip-royalty-notes/
[ga-trade]: https://www.gremlinarchive.com/index.php/2016/05/23/early-tradeshow-leaflet/
[ga-photo]: https://www.gremlinarchive.com/index.php/2016/06/02/anthony-clarke-photograph/
[ga-me]: https://www.gremlinarchive.com/index.php/2017/07/31/a-gremlin-in-the-works-anthony-clarke/
[ga-xr]: https://www.gremlinarchive.com/index.php/2016/11/01/xargons-revenge-c16plus4/
[ga-xw]: https://www.gremlinarchive.com/index.php/2016/05/24/xargon-wars-trade-promotion/
[ga-classics]: https://www.gremlinarchive.com/index.php/2021/02/13/c16-classics/
[ga-omnibus]: https://www.gremlinarchive.com/index.php/2021/12/20/c16-omnibus/
