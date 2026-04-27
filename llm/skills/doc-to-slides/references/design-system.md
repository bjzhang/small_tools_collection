# Design System

All four renderers apply the same defaults, so swapping output formats keeps the deck visually consistent.

## Default theme — Nexus (neutral, accessible)

| Role | Hex | Notes |
|---|---|---|
| Background | `#F7F6F2` | Warm off-white. Page surface. |
| Surface | `#FBFBF9` | Code blocks, cards. |
| Border | `#D4D1CA` | Card outlines. |
| Text | `#28251D` | Body. WCAG AA on bg. |
| Muted | `#7A7974` | Captions, secondary text. |
| Accent | `#01696F` | Hydra teal — links, headings, stat values. **Single accent only.** |

Stored in `assets/theme.default.json`.

## Fonts

| Slot | PPTX | Marp / Slidev / Reveal |
|---|---|---|
| Heading | Calibri Bold | Inter (CDN) |
| Body | Calibri | Inter (CDN) |
| Mono | Consolas | JetBrains Mono (CDN) |

PPTX cannot embed fonts — Calibri ships with Office and is the safest cross-platform default. Web renderers load Inter from Google Fonts so output looks identical on any browser.

## Sizes

| Element | PPTX (pt) | Web (px equiv.) |
|---|---|---|
| Cover title | 56 | 88 |
| Slide title | 32–36 | 56 |
| Body bullets | 18 | 32 |
| Captions / footer | 11–12 | 20 |
| Stat value | 140 | 240 |

## Spacing (PPTX)

- Slide: 13.333" × 7.5" (16:9 wide).
- Margins: 0.55" on every side.
- Gap between elements: 0.3" minimum, 0.5" preferred.

## Custom themes

When the user supplies a brand color or the topic suggests one (finance → navy, sustainability → forest green, healthcare → calming blue), pass an override file:

```bash
node scripts/render-pptx.js outline.json out.pptx ./brand-theme.json
```

`brand-theme.json` only needs the keys you're overriding:

```json
{
  "colors": {
    "accent": "#0B3D91",
    "text":   "#0F1A2C"
  }
}
```

Always keep **one accent** color. Adding a second accent breaks the visual hierarchy.

## What to avoid

- Multiple accents — the eye no longer knows where to look.
- Accent lines under titles — a hallmark of AI-generated slides. Use whitespace.
- Colored side-borders on cards (`border-left: 3px solid …`) — same problem.
- Gradient backgrounds on shapes — solid colors are more professional.
- Decorative icons next to bullets — only include icons if data demands it (chart legend, logo).
- Bullets on titles, stats, or single-sentence callouts. Bullets are for true lists of 3+ items.
- Generic filler ("Empowering your journey", "Unlock the power of…").
