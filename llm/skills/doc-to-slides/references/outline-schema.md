# Outline JSON Schema

The planner (Stage 2) produces a JSON object matching this schema. All four renderers consume it without modification.

## Top-level

```jsonc
{
  "title": "string — used for HTML <title> only; cover slide has its own title",
  "footer": "string — appears on every content slide. Recommended: '<source-doc-name> · YYYY-MM-DD'",
  "theme": { /* optional override; merged over assets/theme.default.json */ },
  "slides": [ /* array of slide objects, see below */ ]
}
```

## Slide objects — by `type`

Every slide has a `type`. Required and optional fields per type:

### `cover`

```jsonc
{
  "type": "cover",
  "title": "string (required) — primary deck title",
  "subtitle": "string (optional)",
  "footer": "string (optional) — author, date, source-doc-name"
}
```

### `agenda`

```jsonc
{
  "type": "agenda",
  "title": "string (optional, default: 'Agenda')",
  "items": ["string", "..."]   // 3–8 items
}
```

### `section`

Visual divider. No body content. Use to break the deck into 2–4 acts.

```jsonc
{ "type": "section", "title": "string (required)" }
```

### `bullets`

Default content slide.

```jsonc
{
  "type": "bullets",
  "title": "string (required) — write as a claim, not a label",
  "bullets": ["string ≤ 14 words", "..."]   // max 6
}
```

### `two-column`

Compare-and-contrast layout.

```jsonc
{
  "type": "two-column",
  "title": "string (required)",
  "left":  { "heading": "string", "items": ["string", "..."] },  // max 6
  "right": { "heading": "string", "items": ["string", "..."] }   // max 6
}
```

### `stat`

Single dominant number. No bullets.

```jsonc
{
  "type": "stat",
  "value": "string — '23%', '$4.1M', '12×'",
  "caption": "string — what the number means"
}
```

### `quote`

Pulled quote with optional attribution.

```jsonc
{
  "type": "quote",
  "quote": "string (required)",
  "attribution": "string (optional) — speaker, role, date"
}
```

### `code`

Dedicated code slide. Never mix code with bullets.

```jsonc
{
  "type": "code",
  "title": "string (required)",
  "language": "string (optional) — 'python', 'yaml', 'bash', 'typescript'",
  "code": "string (required) — verbatim. ≤ 18 lines, ≤ 80 chars wide"
}
```

### `image`

Single figure with caption.

```jsonc
{
  "type": "image",
  "title": "string (required)",
  "path": "string (required) — absolute path or URL the renderer can read",
  "caption": "string (optional)"
}
```

### `closing`

Final slide. No bullets.

```jsonc
{
  "type": "closing",
  "title": "string (optional, default: 'Thank you.')",
  "subtitle": "string (optional) — call to action, decision needed, contact",
  "quote": "string (optional)",
  "quoteAttribution": "string (optional)",
  "links": [["label", "url"], "..."]   // optional, max 4 — pill row of useful URLs
}
```

---

## Editorial slide types

These types unlock the engineering-editorial style described in `references/editorial-style.md`. They require `theme.editorial.json` (or any theme that defines `accent`, `accentSoft`, `warn`, `warnSoft`, `surface`, `border`). Renderers without editorial support fall back to the closest standard type.

Every editorial slide accepts these optional fields in addition to its required ones:

- `kicker` — short ALL-CAPS eyebrow above the title (≤ 6 words).
- `time` — speaker cue label like `~3:45` shown in the top-right pill (used when this deck is presented; ignored when exported as handout).
- `note` — italic muted aphorism shown below the main composition (≤ 18 words).
- `sources` — array of `[label, url]` pairs rendered as a hyperlinked source line.

### `frozen-vs-mutable`

Claim-as-headline slide with two equal panels. The signature move of the editorial style.

```jsonc
{
  "type": "frozen-vs-mutable",
  "kicker": "string (optional)",
  "title": "string (required) — write as two short sentences ending in periods",
  "frozen": { "label": "string", "items": ["string", "..."] },   // max 5
  "mutable": { "label": "string", "items": ["string", "..."] },  // max 5
  "note": "string (optional)"
}
```

### `kpi-row`

Three KPI tiles across the top half. Use after a kicker+title to anchor a slide in numbers.

```jsonc
{
  "type": "kpi-row",
  "kicker": "string (optional)",
  "title": "string (required)",
  "subtitle": "string (optional)",
  "tiles": [                              // exactly 3
    { "value": "100%", "label": "RVA23 MANDATORY COVERAGE", "variant": "accent" },
    { "value": "v7.0-rc1", "label": "RELEASED 2026-02-22" },
    { "value": "60+", "label": "REDDIT UPVOTES" }
  ],
  "cards": [                              // optional, max 4 — 2x2 grid below tiles
    { "label": "PRIMARY DRIVER", "body": "...", "variant": "accent" },
    { "label": "OPEN ISSUE", "body": "...", "variant": "warn" }
  ],
  "note": "string (optional)"
}
```

### `mcard-grid`

2×2 or 1×N grid of cards. Each card has a label, body, and optional variant (`neutral` | `accent` | `warn`).

```jsonc
{
  "type": "mcard-grid",
  "kicker": "string (optional)",
  "title": "string (required)",
  "subtitle": "string (optional)",
  "cards": [                              // 3 or 4
    { "label": "REQUIRED", "body": "V, H, AIA, Zic*", "variant": "accent" },
    { "label": "BENCHMARK", "body": "riscv64 dual-core boot" }
  ]
}
```

### `extension-table`

Left-anchored mandatory list (tag + name + sublabel rows). Pairs well with right-side narrative card or KPI.

```jsonc
{
  "type": "extension-table",
  "kicker": "string (optional)",
  "title": "string (required)",
  "label": "string (optional, default: 'Mandatory')",
  "rows": [                                // 4–6
    { "tag": "V", "name": "Vector extension", "sub": "AI/ML, crypto, data parallel" },
    { "tag": "H", "name": "Hypervisor", "sub": "KVM-class virtualization" }
  ],
  "sideCard": {                            // optional — narrative card to the right
    "label": "WHY IT MATTERS",
    "body": "string",
    "variant": "accent"
  },
  "sideKpi": { "value": "10+", "label": "MANDATORY EXTENSIONS" }   // optional
}
```

### `layer-stack`

Three stacked panels representing layers / steps / principles. Top panel typically uses `accent` variant.

```jsonc
{
  "type": "layer-stack",
  "kicker": "string (optional)",
  "title": "string (required)",
  "layers": [                              // exactly 3
    { "label": "LAYER 1 · IMMUTABLE", "name": "Firmware + kernel + DTB", "sub": "Byte-identical across runs", "variant": "accent" },
    { "label": "LAYER 2 · TEST IMAGE", "name": "Workload + datasets", "sub": "cpio + ext4" },
    { "label": "LAYER 3 · INTENT", "name": "Kernel cmdline", "sub": "Parsed by task-runner.sh" }
  ],
  "companion": [                           // optional — 3 mcards on the right
    { "label": "PROPERTY", "body": "Storage-media agnostic" }
  ]
}
```

### `comparison`

Side-by-side conceptual comparison. Renders as a two-column table with kicker labels.

```jsonc
{
  "type": "comparison",
  "kicker": "string (optional)",
  "title": "string (required)",
  "leftLabel": "string",
  "rightLabel": "string",
  "rows": [                                // 4–7
    ["Concept", "Container distribution", "Split-image validation"],
    ["Immutable layers", "image layers", "firmware + kernel + DTB"]
  ]
}
```

### `ascii-diagram`

Monospace block (memory map, pipeline, ASCII art). Renders inside a `surface` card.

```jsonc
{
  "type": "ascii-diagram",
  "kicker": "string (optional)",
  "title": "string (required)",
  "label": "string (optional) — caption above the block",
  "diagram": "string (required) — multi-line, monospace, ≤ 18 lines, ≤ 88 cols",
  "legend": [                              // optional — pill row below diagram
    { "label": "OpenSBI", "variant": "accent" },
    { "label": "Host kernel" }
  ]
}
```

---

## Validation rules the planner enforces

Before writing `outline.json`:

1. First slide is `cover`. Last is `closing`.
2. No `bullets` slide has more than 6 bullets, or any bullet > 14 words. If the source can't be compressed, **split into two slides**.
3. No two consecutive slides have identical titles.
4. If the source has any numeric claim (`%`, `$`, `×`, "X times faster"), at least one `stat` slide exists.
5. If code blocks appear in the source, they get `code` slides — never inline in `bullets`.
6. Total slide count is 8–18. If the source produces > 18, emit a warning in the agent's response and offer a "summary deck" plus an "appendix deck" split.
7. Every slide except `cover`, `section`, and `closing` shows the deck-level `footer`.
