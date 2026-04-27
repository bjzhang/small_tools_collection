# Renderer-Specific Notes

Behaviors that surprise people the first time they hit them.

## PPTX (`render-pptx.js`)

- **Fonts cannot be embedded** in `.pptx`. The skill defaults to Calibri because every Office install has it. If a viewer opens the file on a system without Calibri, PowerPoint substitutes — usually fine, but text widths shift slightly.
- **LibreOffice ≠ PowerPoint** for text wrapping. The PDF you get from `soffice --headless --convert-to pdf` may show wraps that don't appear in real PowerPoint, and vice versa. When QA flags wrap bugs, also open the file in PowerPoint or Keynote if available.
- **`charSpacing` + `Consolas`** can split English short labels into per-character chunks under LibreOffice. The default theme avoids this combo. If you override fonts, drop `charSpacing` from any short-text element.
- **Image `sizing.contain`** preserves aspect ratio inside the bounding box. Use it on the `image` slide type — never set raw `w` and `h` from the source dimensions.

## Marp (`render-marp.js`)

- **Triple-backtick code blocks consume the whole slide** in Marp. The skill always emits code on a dedicated `code` slide — don't try to inline.
- **Pagination footer collides with custom HTML footers.** The skill turns Marp's built-in pagination on (`paginate: true`) and uses Marp's `footer:` directive — don't add a manual footer in slide markdown.
- **`<!-- _class: section -->`** changes the next slide's class only. The skill writes one directive per section — verify it's at the top of that slide if you edit by hand.

## Slidev (`render-slidev.js`)

- **`layout: two-cols`** uses `::right::` as the column break. Don't add a closing marker — the next `---` ends the slide.
- **`layout: image-right`** requires the `image:` URL to be reachable from Slidev's dev server. For local files, prefer absolute paths during dev; for shipping, copy images into the project's `public/` folder.
- **Slidev requires `npm i @slidev/cli`** — it's not bundled. The skill emits the markdown but doesn't run Slidev.

## Reveal.js (`render-reveal.js`)

- **Output is single-file HTML** with CDN links. Works offline only after the CDN resources are cached. For true offline decks, vendor `reveal.js`, the theme CSS, and the highlight CSS into the same directory and rewrite the URLs.
- **`Reveal.slide(idx)`** in the screenshot script jumps without animation (third arg `0` = no transition). If you change the script to use real transitions, increase the `waitForTimeout` from 150ms to ≥ 600ms.
- **Code blocks use Highlight.js** via the CDN plugin. Languages outside its default bundle won't highlight. Common languages — `python`, `bash`, `yaml`, `typescript`, `rust`, `go` — all work out of the box.
- **Images:** `max-height: 60vh` is set in the inline CSS so tall figures don't push titles offscreen.

## Common to all renderers

- **Outline JSON drives everything.** If you find yourself special-casing markdown after rendering, the fix belongs in the outline JSON, not the renderer.
- **Theme overrides merge shallowly.** `{ "colors": { "accent": "#…" } }` merges with the default `colors` block, but a top-level key replaces the whole sub-object. To override one font slot, copy the full `fonts` block first.
- **Footer suppression on cover/section/closing** is hardcoded. If you want a footer on those slides, edit the renderer — don't try to express it in JSON.
