# History and Credits

## Xargon Wars

Xargon Wars is a Commodore 16 shoot-'em-up that I wrote at Micro Projects, and Gremlin Graphics published it on cassette. You command a gun turret at the bottom of the screen against sixteen sheets of attacking aliens and their laser bombs, and you have to watch a laser temperature gauge that cuts out your fire when it overheats.

I'm writing this history only from evidence that has survived: the source, the disk and the packaging. I haven't added my own recollections yet. When I do, they'll be dated and kept separate from the evidence below.

---

## What the Evidence Says

The source header in `ULTRA` (the root module) reads:

```text
; WITH KIND PERMISSION FROM
;
; JOHN B MARSHALL
;
; AND WRITTEN BY A.J.CLARKE
;
; (C) MICRO-PROJECTS LTD. 1985
```

I've kept that wording exactly as it is, and I haven't assigned John B Marshall a role the source doesn't state. The root module and its banner are called `ULTRA`, while the game's own text says `XARGON`. That suggests `ULTRA` was the project name during development, but nothing on the disk confirms it.

The hand-written label on my source disk reads "XARGON WARS C16 / © MICRO PROJECTS '85 / SOURCE FILES / COMPLETED 22/1/85". The disk's own header says `PEUGEOT 205 GTI` with ID `85`.

The title page scroller in `SCROLL-BUFFER` reads, line by line as stored:

```text
 WRITTEN BY THE SIXTEEN DIVISION OF
MICRO PROJECTS LTD  LOOK OUT FOR THE
 PETALS OF DOOM ALSO FROM GREMLIN
  THANKS TO
MATTHEW FOR THE GRAPHICS AND HIS HELP
 AND ANT FOR HIS INVALUABLE HELP
  HELLO TO VICKI KATH CHRIS JOHN MARK
 JASON SANDRA ALISON ET ALL
```

The title page shows "© GREMLIN GRAPHICS", and the high-score table starts with M.P.L. on 1,000, followed by BEAVER, MONTY, SAM, POTTY and GRUMPY. A source comment in `STARTER` says the idea for starting the stars came from a "'ZALAGA' STYLE GAME SEEN AT THE PUB".

The cassette inlay shows the Gremlin Graphics logo and "Commodore 16", and the instruction card says "16 Screens / Multi Level". [Artifacts](ARTIFACTS.md) describes them in full.

### Dates

The 1985 notices and the disk label's "COMPLETED 22/1/85" date the source to January 1985, and the disk ID `85` fits with that. The 7 October 1992 dates on the `DISK7A` folder and its `INDEX` belong to that later PC export. The 2014 file date on `xargon_wars.prg` belongs to the single-file copy, not to the game.

---

## The Gremlin Archive and the Book

Mark Hardisty's book *A Gremlin in the Works* (Bitmap Books), the officially endorsed history of Gremlin Graphics, tells the Micro Projects story, and I contributed to it. His [Gremlin Graphics Archive](https://www.gremlinarchive.com/) publishes my 1992 export of the development disks, including this game's `DISK7A` and the hack version on `DISK7B`, and has a [Xargon Wars – Trade Promotion](https://www.gremlinarchive.com/index.php/2016/05/24/xargon-wars-trade-promotion/) post. [Gremlin Archive and the Book](GREMLIN_ARCHIVE.md) has the references, the archive's disk list and how this project's files match it.

---

## Recovery Background and Build Template

My original C64/1541 development setup and the later source recovery are written up in my [Dorks Dilemma C16 repository](https://github.com/anthonyjclarke/Dorks_Dilemma_C16). Its [Development History](https://github.com/anthonyjclarke/Dorks_Dilemma_C16/blob/main/docs/DEVELOPMENT_HISTORY.md) has my recollections and the acknowledgements for the recovery tools. The C64 editor, DOS wedge, fast loader and assembler on this disk come from that same setup.

This project adapts the disk reader, source conversion, ca65/ld65 build, PlatformIO integration and VICE monitor approach from Dorks Dilemma and Tycoon Tex. Xargon Wars' sources, memory layout, object listing and running-version comparison have all been validated separately here.

---

## Tool Acknowledgements

The modern build uses the [cc65 toolchain](https://cc65.github.io/), the [VICE emulator](https://vice-emu.sourceforge.io/), [PlatformIO](https://platformio.org/), [Visual Studio Code](https://code.visualstudio.com/) and Python. The reassembly and emulator checks depend on the people who write and maintain them.

All the historical copyright notices in the source, the binaries and the printed material are still in place. See [Rights and Preservation](../RIGHTS.md).
