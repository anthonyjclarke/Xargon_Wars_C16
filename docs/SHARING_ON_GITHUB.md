# Sharing on GitHub

## Repository

The public repository is [anthonyjclarke/Xargon_Wars_C16](https://github.com/anthonyjclarke/Xargon_Wars_C16). I work on `main`. The annotated tag `v1.0.0` marks the verified preservation build.

`.gitignore` leaves out generated output, PlatformIO caches, Python caches and macOS metadata. It deliberately keeps the D64 image, the extracted `.seq` and `.prg` files, the 1992 export and its ZIP, the running PRG and the artwork. `.gitattributes` turns off text conversion, whitespace handling and diffs for both preserved input folders. That protects the CR-only disk text and the CRLF 1992 export.

The README links to the build instructions, validation, history, artifact catalogue and the Dorks Dilemma recovery story. `RIGHTS.md` records the historical notices I've kept, and I haven't assigned a new licence. The [Changelog](../CHANGELOG.md) lists each release with its commit and tag.

---

## Final Local Checks

Run these from the project root:

```sh
./build.sh
make test
pio run -e c16 -e c16_debug
make verify
git status --short
```

The first three need Python, cc65 and PlatformIO. `make verify` also needs VICE and a graphical desktop. [Source and Validation](SOURCE_AND_VALIDATION.md) and [Testing](../TESTING.md) record the current results and the limits of the verification.

The reports in `docs/verification/` and the screenshots in `docs/images/` belong to the documented checkpoint. To refresh them after a reviewed change, rerun the checks, then copy the evidence across with the number of passing tests and the date:

```sh
python3 scripts/publish_evidence.py --tests-passed 11 --date 2026-10-20
```

---

## Clone or Update

```sh
git clone https://github.com/anthonyjclarke/Xargon_Wars_C16.git
cd Xargon_Wars_C16
git switch --detach v1.0.0
```

For later work, go back to `main`, review the changes, run the relevant checks, then commit and push:

```sh
git switch main
git add .
git diff --cached --stat
git commit -m "type(scope): describe the change"
git push origin main
```

On every push and pull request, GitHub Actions runs the source build, the running-version comparison, the regression tests, both PlatformIO environments and the output agreement check. It uploads the rebuilt PRG and reports as a workflow artifact. It doesn't run a graphical emulator. Results are on the repository's [Actions page](https://github.com/anthonyjclarke/Xargon_Wars_C16/actions).

---

## Version Tags

`v1.0.0` is the verified preservation build. Later verified checkpoints get new annotated tags. Leave published tags alone, so that their source, documentation and recorded evidence can still be reproduced.
