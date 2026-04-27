#!/usr/bin/env node
// render-slidev.js — outline JSON → Slidev Markdown.
// usage: node render-slidev.js <outline.json> <out.slidev.md> [theme.json]

const fs = require("fs");
const path = require("path");

const [, , outlinePath, outPath, themePath] = process.argv;
if (!outlinePath || !outPath) {
  console.error("usage: render-slidev.js <outline.json> <out.slidev.md> [theme.json]");
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

function header() {
  return [
    "---",
    "theme: default",
    "lineNumbers: false",
    "drawings:",
    "  persist: false",
    "transition: slide-left",
    "mdc: true",
    `colorSchema: "light"`,
    "---",
    "",
  ].join("\n");
}

function slideMd(d, idx) {
  switch (d.type) {
    case "cover":
      return [
        "---",
        "layout: cover",
        d.footer ? `class: text-center` : "",
        "---",
        "",
        `# ${d.title}`,
        "",
        d.subtitle ? `${d.subtitle}` : "",
        "",
        d.footer ? `<div class="text-sm opacity-70 mt-8">${d.footer}</div>` : "",
      ].filter(Boolean).join("\n");

    case "section":
      return [
        "---",
        "layout: section",
        "---",
        "",
        `# ${d.title}`,
      ].join("\n");

    case "bullets":
      return [
        "---",
        "layout: default",
        "---",
        "",
        `# ${d.title}`,
        "",
        ...(d.bullets || []).slice(0, 6).map((b) => `- ${b}`),
      ].join("\n");

    case "two-column":
      return [
        "---",
        "layout: two-cols",
        "---",
        "",
        `# ${d.title}`,
        "",
        `## ${d.left.heading}`,
        "",
        ...(d.left.items || []).slice(0, 6).map((i) => `- ${i}`),
        "",
        "::right::",
        "",
        `## ${d.right.heading}`,
        "",
        ...(d.right.items || []).slice(0, 6).map((i) => `- ${i}`),
      ].join("\n");

    case "stat":
      return [
        "---",
        "layout: center",
        "---",
        "",
        `<div class="text-9xl font-bold" style="color:${C.accent}">${d.value}</div>`,
        "",
        `<div class="text-2xl mt-4 opacity-80">${d.caption}</div>`,
      ].join("\n");

    case "quote":
      return [
        "---",
        "layout: quote",
        "---",
        "",
        `# "${d.quote}"`,
        "",
        d.attribution ? `<div class="opacity-70">— ${d.attribution}</div>` : "",
      ].filter(Boolean).join("\n");

    case "code":
      return [
        "---",
        "layout: default",
        "---",
        "",
        `# ${d.title}`,
        "",
        `\`\`\`${d.language || ""}`,
        d.code,
        "```",
      ].join("\n");

    case "image":
      return [
        "---",
        "layout: image-right",
        `image: ${d.path}`,
        "---",
        "",
        `# ${d.title}`,
        "",
        d.caption ? `<div class="opacity-70 italic">${d.caption}</div>` : "",
      ].filter(Boolean).join("\n");

    case "agenda":
      return [
        "---",
        "layout: default",
        "---",
        "",
        `# ${d.title || "Agenda"}`,
        "",
        ...(d.items || []).map((it, i) => `${i + 1}. ${it}`),
      ].join("\n");

    case "closing":
      return [
        "---",
        "layout: end",
        "---",
        "",
        `# ${d.title || "Thank you."}`,
        "",
        d.subtitle ? d.subtitle : "",
      ].filter(Boolean).join("\n");

    default:
      throw new Error(`unknown slide type: ${d.type}`);
  }
}

const body = outline.slides.map(slideMd).join("\n\n");
fs.writeFileSync(outPath, header() + body + "\n");
console.error(`wrote ${outPath} (${outline.slides.length} slides)`);
