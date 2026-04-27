#!/usr/bin/env node
// render-reveal.js — outline JSON → self-contained Reveal.js HTML.
// usage: node render-reveal.js <outline.json> <out.html> [theme.json]
//
// Output is single-file: pulls reveal.js from CDN, inlines theme styles.

const fs = require("fs");
const path = require("path");

const [, , outlinePath, outPath, themePath] = process.argv;
if (!outlinePath || !outPath) {
  console.error("usage: render-reveal.js <outline.json> <out.html> [theme.json]");
  process.exit(64);
}

const outline = JSON.parse(fs.readFileSync(outlinePath, "utf8"));
const defaultTheme = JSON.parse(
  fs.readFileSync(path.join(__dirname, "..", "assets", "theme.default.json"), "utf8")
);
const theme = themePath
  ? { ...defaultTheme, ...JSON.parse(fs.readFileSync(themePath, "utf8")) }
  : defaultTheme;

const C = theme.colors;

const esc = (s) =>
  String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

function slideHtml(d) {
  switch (d.type) {
    case "cover":
      return `<section class="cover"><h1>${esc(d.title)}</h1>${d.subtitle ? `<p class="subtitle">${esc(d.subtitle)}</p>` : ""}${d.footer ? `<p class="footer-meta">${esc(d.footer)}</p>` : ""}</section>`;

    case "section":
      return `<section data-background-color="${C.accent}" class="section"><h1>${esc(d.title)}</h1></section>`;

    case "bullets":
      return `<section><h2>${esc(d.title)}</h2><ul>${(d.bullets || []).slice(0, 6).map((b) => `<li>${esc(b)}</li>`).join("")}</ul></section>`;

    case "two-column":
      return `<section><h2>${esc(d.title)}</h2><div class="two-col"><div><h3>${esc(d.left.heading)}</h3><ul>${(d.left.items || []).slice(0, 6).map((i) => `<li>${esc(i)}</li>`).join("")}</ul></div><div><h3>${esc(d.right.heading)}</h3><ul>${(d.right.items || []).slice(0, 6).map((i) => `<li>${esc(i)}</li>`).join("")}</ul></div></div></section>`;

    case "stat":
      return `<section class="stat"><div class="stat-value">${esc(d.value)}</div><div class="stat-caption">${esc(d.caption)}</div></section>`;

    case "quote":
      return `<section class="quote"><blockquote>${esc(d.quote)}</blockquote>${d.attribution ? `<p class="attribution">— ${esc(d.attribution)}</p>` : ""}</section>`;

    case "code":
      return `<section><h2>${esc(d.title)}</h2><pre><code class="language-${esc(d.language || "")}" data-trim>${esc(d.code)}</code></pre></section>`;

    case "image":
      return `<section><h2>${esc(d.title)}</h2><img src="${esc(d.path)}" alt="${esc(d.title)}"/>${d.caption ? `<p class="caption">${esc(d.caption)}</p>` : ""}</section>`;

    case "agenda":
      return `<section><h2>${esc(d.title || "Agenda")}</h2><ol>${(d.items || []).map((it) => `<li>${esc(it)}</li>`).join("")}</ol></section>`;

    case "closing":
      return `<section class="closing"><h1>${esc(d.title || "Thank you.")}</h1>${d.subtitle ? `<p class="subtitle">${esc(d.subtitle)}</p>` : ""}</section>`;

    default:
      throw new Error(`unknown slide type: ${d.type}`);
  }
}

const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>${esc(outline.title || "Deck")}</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css"/>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/white.css" id="theme"/>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/monokai.css"/>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=JetBrains+Mono&display=swap" rel="stylesheet">
<style>
  .reveal { font-family: 'Inter', system-ui, sans-serif; color: ${C.text}; background: ${C.bg}; }
  .reveal h1, .reveal h2, .reveal h3 { font-family: 'Inter', system-ui, sans-serif; color: ${C.text}; text-transform: none; letter-spacing: 0; }
  .reveal h1 { font-size: 2.6em; line-height: 1.1; }
  .reveal h2 { font-size: 1.8em; }
  .reveal h3 { color: ${C.accent}; }
  .reveal section.cover { text-align: left; }
  .reveal section.cover h1 { font-size: 3.2em; }
  .reveal section.cover .subtitle { font-size: 1.4em; color: ${C.muted}; margin-top: 0.5em; }
  .reveal section.cover .footer-meta { color: ${C.accent}; margin-top: 2em; font-size: 0.7em; }
  .reveal section.section h1 { color: ${C.bg}; text-align: center; }
  .reveal section.stat .stat-value { font-size: 7em; font-weight: 700; color: ${C.accent}; text-align: center; line-height: 1; }
  .reveal section.stat .stat-caption { font-size: 1.2em; text-align: center; margin-top: 0.5em; }
  .reveal section.quote blockquote { border-left: 4px solid ${C.accent}; padding-left: 0.8em; font-size: 1.4em; font-style: italic; }
  .reveal section.quote .attribution { color: ${C.muted}; margin-top: 0.5em; }
  .reveal section.closing { text-align: center; }
  .reveal pre { font-family: 'JetBrains Mono', monospace; font-size: 0.5em; box-shadow: none; background: ${C.surface}; border: 1px solid ${C.border}; border-radius: 6px; }
  .reveal code { font-family: 'JetBrains Mono', monospace; }
  .reveal .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 2em; text-align: left; }
  .reveal .caption { font-size: 0.6em; color: ${C.muted}; font-style: italic; }
  .reveal img { max-height: 60vh; }
  .reveal ul, .reveal ol { display: block; }
</style>
</head>
<body>
<div class="reveal">
  <div class="slides">
    ${outline.slides.map(slideHtml).join("\n    ")}
  </div>
</div>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
<script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/plugin/highlight/highlight.js"></script>
<script>
  Reveal.initialize({
    hash: true,
    width: 1280,
    height: 720,
    margin: 0.06,
    plugins: [RevealHighlight]
  });
</script>
</body>
</html>
`;

fs.writeFileSync(outPath, html);
console.error(`wrote ${outPath} (${outline.slides.length} slides)`);
