# Maintaining the HTML Documentation

## Source of Truth

The [complete HTML handbook](XARGON_WARS.html) gathers the current Markdown guides, artifact catalogue, validation notes, codebase analysis, porting guide and generated code reference into one document. The images, styling, reader controls and Mermaid diagram renderer are all embedded, so it opens in a browser with no internet connection.

**Edit the Markdown, never the generated HTML.** The generator doesn't keep a second copy of the prose. Each chapter links to its Markdown source, and links between included documents become links within the page. Links to scripts, JSON files and other repository files are relative, so they only work when the checkout sits next to the HTML.

The handbook has a contents sidebar, chapter search, image enlargement (click an image, then use "Full resolution") and print support.

---

## Regeneration

The generator needs Node.js 20 or later. Its Markdown parser and diagram renderer are vendored in `scripts/vendor/` with their licences. It doesn't use npm or download anything.

| Command           | What it does                                |
|:------------------|:--------------------------------------------|
| `make docs`       | Build, refresh the analysis, write HTML     |
| `make docs-html`  | Write HTML from current Markdown and images |
| `make docs-watch` | Rewrite HTML whenever an input changes      |
| `make docs-check` | Fail if the saved HTML is missing or stale  |
| `make test-docs`  | Run the documentation tests                 |

`node scripts/build_docs.mjs` is the direct equivalent of `make docs-html`, and accepts `--check` or `--watch`. If Node isn't on the normal path, use `make docs-html NODE=/path/to/node`.

The output is `docs/XARGON_WARS.html`. Commit it together with the Markdown and asset changes, so the published copy is always current.

`make docs` doesn't redraw the graphics figures, recapture the palette or rerun the VICE probes, because those need Pillow or VICE. After changing the asset data, run `python3 scripts/render_game_graphics.py` and then `make docs-html`. The [analysis README](analysis/README.md) explains each generator.

### Watching Edits

`make docs-watch` polls the Markdown, images, configuration and templates, and regenerates the HTML when any of them change. Refresh the browser to see the result, and press Ctrl+C to stop. It doesn't rebuild the game or the analysis. Restart it after changing the chapter list.

### Checking Freshness

`make docs-check` regenerates the HTML in memory and compares it with the saved file without overwriting it. It catches any change to the Markdown, embedded images, templates, configuration or renderer files. `make test-docs` checks link rewriting, duplicate headings, embedded images, failure on broken links and remote images, HTML escaping, determinism, freshness of the saved handbook and watch mode.

---

## Chapter Selection and Presentation

`docs/handbook.json` sets the reading order: the project guide first (history, artifacts, building, testing, validation, analysis, porting), then reference and maintenance material. A new Markdown guide only appears once it's added there. `CLAUDE.md` is deliberately left out, because it's guidance for coding assistants rather than documentation.

`scripts/build_docs.mjs` does the conversion. It namespaces headings by document, rewrites links, embeds local images as data URIs, and fails on a broken link or missing section. Raw HTML in Markdown is escaped. The page layout and controls are in `scripts/docs/handbook.html`, `handbook.css` and `handbook.js`. Mermaid code blocks render in the browser from the embedded library, and the diagram source stays available under each diagram.

Generation is deterministic and doesn't include a timestamp. The handbook's "source revision" is the first 12 hex digits of a SHA-256 digest over the hashes of every input file. Those hashes are listed in the page's `source-provenance` JSON block. That identifies the documentation snapshot. It says nothing new about the game build or about gameplay testing.

The source-disk photo is 3024 pixels tall and about 1 MB, so the handbook is several megabytes. That's expected.

---

## Third-Party Renderers

The generator uses [Marked](https://marked.js.org/) 17.0.5 to convert Markdown, and the HTML embeds [Mermaid](https://mermaid.js.org/) 10.9.3 for diagrams. Both are pinned, and their licences are in `scripts/vendor/` and in the handbook's notices. I adapted the generator and templates from my Tycoon Tex restoration.
