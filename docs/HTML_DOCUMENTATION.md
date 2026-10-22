# Maintaining the HTML Documentation

## Source of Truth

The [complete HTML handbook](XARGON_WARS.html) gathers the current Markdown guides, artifact catalogue, validation notes, codebase analysis, porting guide and generated code reference into one document. The images, styling, reader controls and Mermaid diagram renderer are all embedded, so it opens in a browser with no internet connection.

**Edit the Markdown, never the generated HTML.** The generator doesn't keep a second copy of the prose. Each chapter links to its Markdown source, and links between included documents become links within the page. Links to scripts, JSON files and other repository files are relative, so they only work when the checkout sits next to the HTML.

The handbook has a contents sidebar, chapter search, image enlargement (click an image, then use "Full resolution") and print support.

---

## Regeneration

The generator needs **Node.js 20 or later**. Its Markdown parser and diagram renderer live in `scripts/vendor/` with their licences. Generating the HTML doesn't use npm, install packages or download anything.

To rebuild the verified game, refresh the generated code analysis and generate the HTML:

```sh
make docs
```

This full refresh also needs the Python and cc65 build tools. If you're only changing documentation, use the current images and generated reference without rebuilding the game:

```sh
make docs-html
```

The direct equivalent is:

```sh
node scripts/build_docs.mjs
```

The output is `docs/XARGON_WARS.html`. Commit the updated HTML together with the Markdown and asset changes, so readers can open it right away. The root README and the other guides link to it.

`make docs` doesn't redraw the graphics figures, recapture the palette or rerun the VICE probes, because those need Pillow or VICE. After changes to the asset data, run `python3 scripts/render_game_graphics.py` first, then `make docs-html`. The [analysis README](analysis/README.md) explains each generator.

### Watching Edits

```sh
make docs-watch
```

The watcher regenerates the HTML whenever Markdown, images, configuration or presentation templates change. Refresh the browser to see the result, and press Ctrl+C to stop. It doesn't rebuild the game or regenerate the code-analysis assets, so run `make docs` after changes that affect those inputs. Restart the watcher after adding a new source directory or changing the chapter configuration.

### Checking Freshness

```sh
make docs-check
make test-docs
```

The freshness check regenerates the expected output in memory and fails if the saved HTML is missing or stale. It compares source text, embedded image bytes, templates, configuration and renderer files, and it never overwrites the HTML. The documentation tests cover link rewriting, duplicate headings, embedded images and diagrams, failure on broken links and remote images, HTML escaping, determinism, freshness of the saved handbook and watch mode. The game regression checks are still available through `make test`.

If Node isn't on the normal executable path, pass its location to Make as `NODE`, for example `make docs-html NODE=/path/to/node`.

---

## Chapter Selection and Presentation

`docs/handbook.json` sets the reading order: the project guide first (history, artifacts, building, testing, validation, analysis, porting), then reference and maintenance material. A new Markdown guide only appears once it's added there. `CLAUDE.md` is deliberately left out, because it's guidance for coding assistants rather than documentation.

`scripts/build_docs.mjs` does the conversion. It namespaces headings by document, rewrites links, embeds local images as data URIs, and fails on a broken link or missing section. Raw HTML in Markdown is escaped. The page layout and controls are in `scripts/docs/handbook.html`, `handbook.css` and `handbook.js`. Mermaid code blocks render in the browser from the embedded library, and the diagram source stays available under each diagram.

Generation is deterministic and doesn't include a timestamp. The handbook's "source revision" is the first 12 hex digits of a SHA-256 digest over the hashes of every input file. Those hashes are listed in the page's `source-provenance` JSON block. That identifies the documentation snapshot. It says nothing new about the game build or about gameplay testing.

The source-disk photo is 3024 pixels tall and about 1 MB, so the handbook is several megabytes. That's expected.

---

## Third-Party Renderers

The generator uses [Marked](https://marked.js.org/) 17.0.5 to convert Markdown, and the HTML embeds [Mermaid](https://mermaid.js.org/) 10.9.3 for diagrams. Both are pinned, and their licences are in `scripts/vendor/` and in the handbook's notices. I adapted the generator and templates from my Tycoon Tex restoration.
