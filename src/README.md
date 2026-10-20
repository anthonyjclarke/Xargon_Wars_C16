# Source Navigation

## Build Inputs

The active assembly source is the 2026 disk image, `Recovered Source/2026/XargonWars-C16-d64copy.d64`. The build reads its files directly and checks them against the extraction in `Recovered Source/2026/XargonWars-C16/`. `ULTRA` is the root module, and its `.LIB` lines name every other module in assembly order. The 1992 export in `Recovered Source/1992/` is a cross-check only.

The generated ca65 source is `build/xargon.s`. It keeps a `; SOURCE: MODULE:LINE` marker wherever the assembly switches modules, so converted code can be traced back to the original disk file and line. The listing, labels, map and debug files are generated next to it.

---

## Preservation Target

I haven't kept a hand-consolidated copy of the game in this folder. The direct build, Makefile, PlatformIO, tests and VS Code tasks all use the same source-selection and conversion path, so editing generated assembly changes nothing on the next build.

[Source Inventory](../docs/SOURCE_INVENTORY.md) lists the active dependencies, [Build and Run](../docs/BUILD_AND_RUN.md) covers the tooling and [Source and Validation](../docs/SOURCE_AND_VALIDATION.md) describes the object-listing checks. If you change the source on purpose, you also have to change the strict preservation checks on purpose. The [Porting Guide](../docs/PORTING_GUIDE.md#protect-the-preservation-build) suggests how to do that without disturbing the preservation build, and the [Codebase Analysis](../CODEBASE_ANALYSIS.md) is the place to start reading.
