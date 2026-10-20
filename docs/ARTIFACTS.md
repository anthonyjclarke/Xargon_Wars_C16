# Artifacts

## Catalogue

`Original Artifacts/` holds four images. I identified each one by looking at what it shows, not from its filename. All four are kept byte for byte.

| File                   | Size        | Content                               |
|:-----------------------|:------------|:--------------------------------------|
| `xargon_wars.jpg`      | 700 × 488   | Cassette inlay, outer side            |
| `xargon_wars_inst.jpg` | 400 × 628   | Cassette instruction card             |
| `xargon_wars_main.gif` | 320 × 200   | In-game screenshot, wave 1            |
| `C16-64_Disks.JPG`     | 2268 × 3024 | Photo of my source disks in their box |

| File                   | SHA-256 (first 16 hex digits) |
|:-----------------------|:------------------------------|
| `xargon_wars.jpg`      | `0b06f173c0b7eb72`            |
| `xargon_wars_inst.jpg` | `df884c0dd00ba8d6`            |
| `xargon_wars_main.gif` | `c266800a5601b202`            |
| `C16-64_Disks.JPG`     | `4f8fdd39b3169d61`            |

The three game images carry 7 September 2003 file dates, and their sizes and names look like the way an online archive would store them. They're probably archive copies rather than my own scans, but I don't know where they came from. The disk photo is my own, dated 11 June 2017.

---

## Cassette Inlay

![Cassette inlay](../Original%20Artifacts/xargon_wars.jpg)

The front shows the title logo over a spaceship cockpit and an explosion, with Gremlin Graphics' logo and "Commodore 16" on the spine panel. The back has three in-game screenshots and the description: defend your mother planet as gunnery commander against waves of aliens and their laser bombs, with each level faster than the last. Someone has written "131" in red ink next to the Gremlin logo, and I don't know what it refers to.

---

## Instruction Card

![Instruction card](../Original%20Artifacts/xargon_wars_inst.jpg)

The card gives the loading steps (`LOAD`, then `RUN`), the joystick and keyboard selection (`J` or `K`), and these keys:

| Action | Key    |
|:-------|:-------|
| Left   | `ESC`  |
| Right  | `1`    |
| Fire   | `F1`   |
| Up     | `F3`   |
| Down   | `HELP` |

They match `KEY-SCAN` in the source. The card lists "16 alien space attackers", laser bombs and the laser temperature gauge. Its scoring table gives 1 to 8 points per alien for sheets 1 to 8, and 10 points from sheet 9 to 16. It promises 200 bonus points for clearing a level and an extra life every 1,000 points and at the end of each level. The [codebase analysis](../CODEBASE_ANALYSIS.md#scoring-extra-lives-rank-and-high-scores) checks those rules against the code.

---

## Gameplay Screenshot

![Archived gameplay screenshot](../Original%20Artifacts/xargon_wars_main.gif)

This 320 × 200 image has no border. It shows sheet 001 with the score, rank, lives and sheet counters, the laser temperature gauge, the player's ship and two blocks of aliens. Its layout matches the restored game in VICE, as you can see in the [verification screenshots](SOURCE_AND_VALIDATION.md#emulator-evidence-and-limits). I'm using it as visual reference only.

---

## Source Disks

![My source disks](../Original%20Artifacts/C16-64_Disks.JPG)

The front disk's label reads "XARGON WARS C16 / © MICRO PROJECTS '85 / SOURCE FILES / COMPLETED 22/1/85". This is the disk captured as `XargonWars-C16-d64copy.d64`. Behind it is a disk labelled "TYCOON TEX – C16 / © MICRO PROJECTS '85", the source of my [Tycoon Tex C16](https://github.com/anthonyjclarke/Tycoon_Tex_C16) restoration. The photo is 3024 pixels tall, so the documentation shows it scaled down.
