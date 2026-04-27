# Editorial-Engineering Style Guide

A high-density technical deck style derived from analysis of a real openEuler RVA23 deck. Use when the source documentation is dense, technical, and benefits from a "each slide is a newspaper page" composition. Pair with `assets/theme.editorial.json`.

## Core principles

1. **Warm canvas, not white.** Background is `#F7F6F2` (paper-warm). Pure white reads as web/screenshots; off-white reads as edited print.
2. **One accent, used sparingly.** Teal `#01696F` is reserved for: kickers, emphasized cards (max 1 per slide), KPI values, and active navigation. If everything is accented, nothing is.
3. **Three-tier type hierarchy.** Eyebrow (kicker, 11pt ALL-CAPS) → headline (28–44pt) → body (12–18pt). Skip a tier and the slide flattens.
4. **Mono is metadata.** Use `Consolas` (or fallback `Courier New`) only for chrome (page numbers, footer, source lines), code blocks, and ASCII diagrams. Never for body. This is a load-bearing typographic signal.
5. **Title as claim, not topic.** "Linux 7.0 — RVA23 mandatory coverage at 100%" is a claim. "Linux 7.0 status update" is a topic. Always prefer the claim.
6. **Italic-muted footer for authorial voice.** A short aphorism in italic muted text below the main composition reads as the slide's takeaway. Use sparingly — at most every 3–4 slides.
7. **Reuse one card primitive.** All boxes (KPI tiles, cards, panels) share rounded rect (radius 0.08″), 1px border, optional accent variant. Visual coherence comes from the primitive, not from per-slide design.

## Color tokens

| Token | Hex | Use |
|---|---|---|
| `bg` | `#F7F6F2` | Slide background (warm off-white) |
| `surface` | `#FBFBF9` | Default card fill |
| `surfaceAlt` | `#F1EFE8` | Pill / chip background, neutral |
| `border` | `#D4D1CA` | Default 1px card border |
| `borderSoft` | `#E4E2DC` | Inner divider lines |
| `text` | `#28251D` | Body ink (warm near-black, never `#000`) |
| `muted` | `#7A7974` | Secondary text, captions, footers |
| `faint` | `#BAB9B4` | De-emphasized labels |
| `accent` | `#01696F` | Single emphasis color (teal) |
| `accentSoft` | `#E0EEEE` | Tinted card fill for emphasized variant |
| `warn` | `#964219` | Caveats, open questions, warnings (warm ochre) |
| `warnSoft` | `#F3E4D9` | Tinted warn fill |

## Type hierarchy

| Element | Size | Weight | Color | Notes |
|---|---|---|---|---|
| Cover title | 56pt | Bold | `text` | Up to 2 lines, hard newline allowed |
| Slide H1 | 28–44pt | Bold | `text` | Use 44pt when 1-line headline; 28pt when info-dense |
| Kicker / eyebrow | 11pt | Bold | `accent` | ALL-CAPS, no letter-spacing tweaks needed in PPTX |
| Subtitle / sub | 13pt | Italic | `muted` | One line under H1 |
| Body | 12pt | Regular | `text` | Default card body |
| Body emphasis | 18pt | Bold | `text` | Bullet lists in major panels (Slide 5 frozen/mutable style) |
| Stat value | 36pt or 140pt | Bold | `accent` | 36pt in tile rows; 140pt for hero stat |
| Stat label | 10pt | Bold | `muted` | ALL-CAPS, sits under value |
| Footer aphorism | 14pt | Italic | `muted` | Centered, full-width, optional |
| Chrome top/bottom | 8.5pt | Regular | `muted` / `faint` | Mono, letter-spaced |
| Source line | 8pt | Regular | `muted` + `accent` for links | Mono, hyperlinked |

For CJK content, swap `heading` and `body` to `Microsoft YaHei` (or `Source Han Sans`). Keep `mono` and `accent` color the same.

## Composition grid

Stage = 13.333″ × 7.5″ (16:9 wide). Inset all content by **0.55″** on each side. Reserve:

- Top **0.55″** for the header strip (logo / brand mark image).
- Bottom **0.35″** for chrome (footer nav + page count).
- Below the H1 zone, the working canvas is roughly **12.2″ × 4.5″**.

Common splits inside the working canvas:
- **2-column 50/50** — frozen vs mutable, before/after.
- **3-column 30/40/30** — mandatory list, narrative card, evidence image.
- **3-row stack** — three layers, three steps, three principles.
- **2×2 grid** — four-quadrant matrix (e.g. four plans, four cards).
- **KPI row + content** — three big stats above the fold, then cards below.

Avoid pure free-form layouts. The grid is the deck's spine.

## Slide-type recipes

### Cover (signature)
- 56pt title (1–2 lines, hard newline).
- Pill row of 5 keywords below title.
- 3 KPI tiles below pills, each with a big value + small ALL-CAPS label.
- Attribution in muted text bottom-right.

### Section / kicker headline
- ALL-CAPS kicker (`accent`), one line.
- 28–44pt H1 below.
- 13pt italic muted subtitle (optional).
- Working canvas below for 2- or 3-column body.

### Frozen vs mutable (claim slide)
- 28–44pt H1 with two short sentences ending in periods (e.g. "Kernel constant. Workload variant.").
- Two equal panels: left filled with `accentSoft`+`accent` border, right filled with `surface`+`border`.
- Each panel: small label top-left, then bullet list in 18pt bold body.
- Italic muted footer aphorism below both panels (optional).

### Mandatory-extension table (left column)
- Per row: short tag (e.g. "V") at 15pt accent bold, name at 12pt bold, sublabel at 9pt muted.
- 4–6 rows max.

### KPI tile row
- 3 tiles, equal width, height ~1.25″.
- One tile uses `accent` variant; others neutral.
- Big value 36pt, small ALL-CAPS label below.

### Card grid (2×2 or 1×N)
- Each card is the `mcard` primitive: rounded rect, label (10pt bold ALL-CAPS), body (12pt).
- Variants: `neutral` (default), `accent` (one card max), `warn` (for caveats).

### Three-layer stack
- Three vertical panels, height ~1.4″, gap 0.15″.
- Top panel typically `accent` variant, others neutral.
- Each: kicker, 18pt bold layer name, 12pt muted description.
- Optional right column with companion mcards.

### Comparison table
- Two columns labeled with kickers (e.g. "Container distribution" vs "Split-image validation").
- 5–7 rows aligning concepts side by side.

### ASCII diagram / address map
- Mono block in `surface` card, 11pt `Consolas`.
- Tight padding, no extra body text inside the card.
- Caption above the card in 10pt muted bold ALL-CAPS.

### Code block (dedicated slide)
- One code block fills 60–70% of working canvas.
- Mono 11–13pt, line numbers optional.
- Three short bullets below the code highlight what to notice.

### Closing / acknowledgments
- Big "Thank you." (44–56pt).
- Italic quote with attribution.
- Pill row of 4 useful URLs.

## Anti-patterns (do not do these)

- ❌ Using accent color for more than one element per slide. The accent is a finger-point, not paint.
- ❌ Pure black text. Use `#28251D`.
- ❌ Pure white background. Use `#F7F6F2`.
- ❌ Body copy in mono. Mono is reserved.
- ❌ Drop shadows or gradients. The style is flat-by-design.
- ❌ Stock icons or clip art. The accent color and typography are the visual interest.
- ❌ More than 6 bullets per panel. Max is 6, target is 3–4.
- ❌ Decorative kickers that don't summarize the slide's category (e.g. "AGENDA" on a non-agenda slide).
- ❌ Mixing the editorial theme with a different deck's color in the same presentation.
