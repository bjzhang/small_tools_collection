---
name: doc-to-slides
description: "Generate a presentation deck from existing documentation. Accepts Markdown, DOCX, or PDF input and emits PPTX, Marp/Slidev Markdown, or Reveal.js HTML output. Use when the user asks to turn docs into slides, build a deck from a README/RFC/spec/whitepaper, summarize a document as a presentation, or convert .md/.docx/.pdf into a slide deck. Enforces strong content rules — one idea per slide, max six bullets — and ships a reusable Node generator plus PDF-render QA loop."
license: MIT
compatibility: "Claude Code. Requires Node.js 18+, Python 3.10+ with markitdown/pdfminer, LibreOffice (soffice) for PPTX→PDF render, and Poppler (pdftoppm) for visual QA. Network access not required."
metadata:
  author: doc-to-slides
  version: '1.0'
---

# Doc → Slides

Convert existing documentation (Markdown, DOCX, PDF) into a polished slide deck (PPTX, Marp, Slidev, or Reveal.js). The skill prescribes how to chunk a document into slide-sized ideas, applies a consistent neutral design system, and ships a Node generator + visual QA loop so output is shippable, not just structurally valid.

---

## When to Use This Skill

Activate this skill when the user asks to:

- Turn a README, RFC, spec, design doc, whitepaper, or runbook into slides
- Convert `.md`, `.docx`, or `.pdf` documentation into a presentation
- Summarize a document as a deck
- Build slides from existing internal documentation
- Generate a "5-minute version" or "exec summary deck" of long-form docs

Do **not** activate for: authoring slides from scratch with no source doc, redesigning an existing deck, or pure note-taking.

---

## Pipeline Overview

```
┌──────────┐   1. normalize    ┌──────────┐   2. plan      ┌──────────┐   3. render     ┌──────────┐   4. QA
│  source  │ ───────────────►  │  unified │ ────────────►  │  outline │ ──────────────► │  deck    │ ───────►
│ md/docx/ │   markitdown +    │ markdown │   slide-sized  │  (JSON)  │   chosen        │ pptx /   │  PDF +
│   pdf    │   pdfminer        │   doc    │   chunks       │          │   renderer      │ marp /   │  pdftoppm
└──────────┘                   └──────────┘                └──────────┘                 │ reveal   │  diff
                                                                                        └──────────┘
```

Every run executes all four stages. Skipping QA is the single most common failure mode — never deliver a deck without inspecting at least the cover, one content slide, and the closing slide as images.

---

## Stage 1 — Normalize input to Markdown

Use `scripts/normalize.sh <input>` to convert any supported input into clean Markdown on stdout.

| Input | Tool used | Notes |
|---|---|---|
| `.md`, `.markdown` | passthrough | Strip `<style>` and HTML comments. |
| `.docx` | `markitdown` (Python) | Preserves headings, lists, tables. |
| `.pdf` | `markitdown` (preferred) → falls back to `pdftotext -layout` | Tables rarely survive — flag in the outline if present. |
| `.html` | `markitdown` | Treat as bonus; skill is not optimized for HTML. |

The script writes normalized Markdown to a temp file and prints the path. Always work from that file in stages 2–4 — never re-parse the original.

```bash
bash scripts/normalize.sh ./input.pdf
# /tmp/doc-to-slides-abc123/normalized.md
```

If normalization warns about lost content (figures, equations, code listings), include those losses in the deck's "Source notes" appendix slide.

---

## Stage 2 — Plan the outline

The planner produces a **slide outline JSON** (see `references/outline-schema.md`) — an array of slide objects each describing one idea, its layout, and its bullets/figures.

### Content rules (non-negotiable)

These rules are what makes the output presentable. Enforce all of them:

1. **One idea per slide.** A heading covering three subtopics becomes three slides.
2. **Max 6 bullets per slide.** If the source has more, split or promote to a follow-up slide.
3. **Bullets ≤ 14 words.** Rewrite — don't crop mid-sentence.
4. **Title is a claim, not a label.** "Revenue grew 23% in Q4" beats "Q4 Revenue".
5. **No bullets on titles, stats, or single-sentence callouts.** Reserve bullets for true lists.
6. **Promote numbers.** Any "X%", "$Y", "Nx faster" deserves a stat-callout slide.
7. **Code blocks → dedicated slide.** Never mix code with bullets.
8. **Tables ≤ 5 columns × 6 rows.** Larger tables become a figure (image) or a `references/` link in the deck.

### Slide types the planner may emit

| `type` | When to use |
|---|---|
| `cover` | First slide — title + subtitle + author/date. |
| `agenda` | Optional, when the deck is > 12 slides. |
| `section` | Visual divider between major sections. |
| `bullets` | Default content slide: title + 2–6 bullets. |
| `two-column` | Compare/contrast, before/after, pros/cons. |
| `stat` | Single big number with caption. |
| `quote` | Pulled quote with attribution. |
| `code` | Code block with language and optional caption. |
| `image` | Single figure with caption. |
| `closing` | Thanks / contact / next steps / Q&A. |

### Default deck shape

For a typical 2,000–8,000 word source, target **10–14 slides**:

1. Cover
2. Agenda *(only if > 12 slides)*
3. Context / problem (1–2 slides)
4. Approach / solution (3–5 slides — split the heaviest section)
5. Results / evidence — at least one `stat` slide
6. Risks or trade-offs
7. Next steps
8. Closing

Save the outline to `outline.json` in the working directory.

---

## Stage 3 — Render

Pick the renderer based on the user's request. If they didn't specify, default to **PPTX**.

| Format | Trigger phrases | Renderer |
|---|---|---|
| **PPTX** | "PowerPoint", "pptx", "deck for the meeting", "send it to my CEO" | `scripts/render-pptx.js outline.json out.pptx` |
| **Marp** | "Marp", "Markdown slides" | `scripts/render-marp.js outline.json out.marp.md` |
| **Slidev** | "Slidev" | `scripts/render-slidev.js outline.json out.slidev.md` |
| **Reveal.js** | "Reveal", "HTML deck", "browser slides" | `scripts/render-reveal.js outline.json out.html` |

All renderers consume the same outline JSON and apply the same design system (`references/design-system.md`). That keeps content portable across formats — re-rendering from another renderer produces a visually consistent deck.

### Design defaults (applied automatically)

- 16:9, 13.333" × 7.5".
- Light theme. Background `#F7F6F2`. Text `#28251D`. Accent `#01696F`. One accent color, the rest neutral.
- Sans-serif throughout. PPTX uses Calibri (system font — PPTX cannot embed). Marp/Slidev/Reveal load Inter via CDN.
- Title 36–44pt. Body 16–18pt. Captions 11–12pt.
- 0.55" minimum margins on PPTX.
- Footer on every content slide: source-doc name + page index.

Override via outline-level `theme` block if the user specifies brand colors or a topic-suggested palette (finance → navy, sustainability → forest green). See `references/design-system.md`.

---

## Stage 4 — QA (required, do not skip)

### 4a. Content QA

Extract text back out of the rendered deck and confirm it matches the outline.

- **PPTX:** `python -m markitdown out.pptx`
- **Marp / Slidev / Reveal:** `cat` the source — the deck *is* the markdown/HTML.

Grep for placeholder leaks before going further:

```bash
python -m markitdown out.pptx | grep -iE "lorem|ipsum|todo|xxx|placeholder|<.*>" || echo "clean"
```

### 4b. Visual QA via subagent

Render the deck to images and have a fresh-eyed subagent inspect them. Do not inspect the images yourself — you've been staring at the outline and will see what you expect, not what's there.

```bash
# PPTX path
soffice --headless --convert-to pdf out.pptx --outdir qa/
pdftoppm -jpeg -r 150 qa/out.pdf qa/s
ls qa/s-*.jpg

# Reveal.js path — use Playwright (scripts/screenshot-reveal.js)
node scripts/screenshot-reveal.js out.html qa/

# Marp / Slidev — use their built-in PDF export, then pdftoppm
```

Then dispatch a subagent with the prompt template in `references/qa-prompt.md`. Fix every issue it finds, re-render, re-check. **Always at least one fix-and-verify cycle**, even if the first pass looks clean — fixes create new problems.

### 4c. Final checks

- [ ] Cover slide shows title, subtitle, author/date, and source doc name.
- [ ] Every content slide has ≤ 6 bullets, each ≤ 14 words.
- [ ] At least one `stat` slide exists if the source contains any numeric claim.
- [ ] Closing slide is present.
- [ ] No text overflow, no placeholder text, no orphan shapes/dots.
- [ ] Footer source attribution present on every content slide.
- [ ] Total slide count: 8–18 (warn the user if outside this range).

---

## Worked Example

**User request:** "Turn `arch-rfc.md` into a 10-slide deck for tomorrow's review."

```bash
# 1. Normalize (already markdown — passthrough strips comments)
NORM=$(bash scripts/normalize.sh ./arch-rfc.md)

# 2. Plan — the agent reads $NORM and writes outline.json following the rules above
#    (planning is an LLM step, not a script — but the JSON schema is fixed)

# 3. Render
node scripts/render-pptx.js outline.json arch-rfc.pptx

# 4. QA
python -m markitdown arch-rfc.pptx | head -80
soffice --headless --convert-to pdf arch-rfc.pptx --outdir qa/
pdftoppm -jpeg -r 150 qa/arch-rfc.pdf qa/s
# → dispatch subagent with references/qa-prompt.md
```

Final outline (excerpt) showing rule application:

```json
[
  { "type": "cover",   "title": "Service Mesh, Take 2", "subtitle": "Why we're moving from sidecar to ambient", "footer": "arch-rfc.md · 2026-04-27" },
  { "type": "section", "title": "Why now" },
  { "type": "bullets", "title": "The sidecar tax got expensive",
    "bullets": ["~12% CPU overhead per pod", "Memory floor doubled in 2025", "Upgrade pain on 4k pods", "On-call paged 6× last quarter"] },
  { "type": "stat",    "value": "12%", "caption": "CPU overhead per pod under sidecar mesh" },
  { "type": "two-column", "title": "Sidecar vs. ambient",
    "left":  { "heading": "Sidecar", "items": ["Per-pod proxy", "Familiar", "12% CPU"] },
    "right": { "heading": "Ambient", "items": ["Per-node ztunnel", "New ops model", "~3% CPU"] } },
  { "type": "code",    "title": "Migration entry point", "language": "yaml",
    "code": "apiVersion: install.istio.io/v1alpha1\nkind: IstioOperator\nspec:\n  profile: ambient" },
  { "type": "bullets", "title": "Risks we're accepting", "bullets": ["L7 gaps until waypoint GA", "New CNI dependency", "Limited multi-cluster story"] },
  { "type": "bullets", "title": "Rollout plan", "bullets": ["Stage 1: dev clusters (week 1–2)", "Stage 2: stage (week 3)", "Stage 3: prod canary 5% (week 4)", "Stage 4: prod 100% (week 6)"] },
  { "type": "closing", "title": "Decision needed", "subtitle": "Approve ambient migration plan by Friday" }
]
```

---

## Common Errors

**Source PDF has no extractable text.** It's a scan. Tell the user explicitly — OCR is out of scope. Suggest they run `ocrmypdf` first.

**Outline has 30+ slides.** The source isn't deck-shaped — it's reference material. Offer two outputs: an 8–10 slide exec summary plus a longer appendix deck. Don't silently truncate.

**Tables don't survive normalization.** If `markitdown` produces malformed pipe-tables, fall back to rendering the table as an image (use the `image` slide type) and link the source for detail.

**PPTX validation passes but slides are visually broken.** Always run stage 4b. LibreOffice text-wrap differs from PowerPoint — long titles in particular will wrap unexpectedly.

**Marp/Slidev fenced code on a slide containing other content.** Marp treats triple-backtick blocks as full-slide. Either move code to a dedicated `code` slide (preferred) or escape inside HTML.

---

## References

| File | When to read |
|---|---|
| `references/outline-schema.md` | Building the outline JSON in stage 2 — full schema, every slide-type's required fields. |
| `references/design-system.md` | Customizing colors, fonts, or theming for a specific brand or topic. |
| `references/qa-prompt.md` | Stage 4b — copy-paste template for the visual QA subagent. |
| `references/renderer-notes.md` | When a renderer behaves unexpectedly (PPTX font fallback, Marp pagination, Reveal speaker notes). |

## Scripts

| File | Purpose |
|---|---|
| `scripts/normalize.sh` | Stage 1 — convert any supported input to Markdown. |
| `scripts/render-pptx.js` | Stage 3 — outline JSON → PPTX via `pptxgenjs`. |
| `scripts/render-marp.js` | Stage 3 — outline JSON → Marp Markdown. |
| `scripts/render-slidev.js` | Stage 3 — outline JSON → Slidev Markdown. |
| `scripts/render-reveal.js` | Stage 3 — outline JSON → self-contained Reveal.js HTML. |
| `scripts/screenshot-reveal.js` | Stage 4b — Playwright-driven slide screenshots for HTML decks. |

## Assets

| File | Purpose |
|---|---|
| `assets/outline.example.json` | A complete outline JSON the planner can copy and modify. |
| `assets/theme.default.json` | The neutral default theme. |
