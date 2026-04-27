# Visual QA Subagent Prompt

Copy-paste template for Stage 4b. Replace `{N}` with the slide count and update the file paths.

---

```
Visually inspect these slides. Assume there are issues — find them.

Check for:
- Text overflow, mid-word wraps, or truncated titles
- Stray dots/circles, orphan shapes, or bullet markers on stats/titles
- Overlapping elements (footer colliding with body, image over text)
- Insufficient margins (< 0.5" from any slide edge)
- Cramped spacing (< 0.3" between blocks)
- Misaligned columns on two-column slides
- Low-contrast text (light text on light, accent on accent)
- Code blocks that wrap mid-line or overflow the code panel
- Stat slides where the number gets cut off or floats off-center
- Footer text that's missing on content slides or present on cover/section
- Leftover placeholder text ("Lorem", "TODO", "<placeholder>")
- Inconsistent type sizes between slides of the same kind

For each slide, list ALL issues found, even minor ones. If a slide is clean, write "Clean."

Then return a summary with:
- Critical issues (blocking, must fix)
- Should-fix issues (consistent patterns)
- Minor cosmetic notes
- Pass count

Read and analyze these images:
1. /abs/path/qa/s-01.jpg  — Expected: cover slide, title "<deck title>"
2. /abs/path/qa/s-02.jpg  — Expected: <slide-2 description from outline>
... continue for all {N} slides ...
```

---

## Why dispatch to a subagent

You wrote the outline. You picked the layouts. If you inspect the images yourself, you'll see what you expected to render — not what actually rendered. A subagent with no prior context catches font fallbacks, wrap bugs, and missing footers that you'll skim past.

After the subagent reports, fix every issue, re-render, and run **at least one more pass** before delivering. Fixes create new problems.
