#!/usr/bin/env node
// render-marp.js — outline JSON → Marp-flavored Markdown.
// usage: node render-marp.js <outline.json> <out.marp.md> [theme.json]

const fs = require("fs");
const path = require("path");

const [, , outlinePath, outPath, themePath] = process.argv;
if (!outlinePath || !outPath) {
  console.error("usage: render-marp.js <outline.json> <out.marp.md> [theme.json]");
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

function frontMatter() {
  return [
    "---",
    "marp: true",
    "theme: default",
    "paginate: true",
    "size: 16:9",
    "style: |",
    `  section { background: ${C.bg}; color: ${C.text}; font-family: Inter, system-ui, sans-serif; padding: 48px 64px; }`,
    `  h1 { color: ${C.text}; font-size: 44px; line-height: 1.15; }`,
    `  h2 { color: ${C.accent}; font-size: 24px; }`,
    `  strong { color: ${C.accent}; }`,
    `  section.section { background: ${C.accent}; color: ${C.bg}; text-align: center; }`,
    `  section.section h1 { color: ${C.bg}; font-size: 56px; }`,
    `  section.stat .stat-value { font-size: 200px; font-weight: 700; color: ${C.accent}; text-align: center; line-height: 1; }`,
    `  section.stat .stat-caption { font-size: 24px; color: ${C.text}; text-align: center; margin-top: 16px; }`,
    `  pre { background: ${C.surface}; border: 1px solid ${C.border}; border-radius: 6px; padding: 16px; font-size: 16px; }`,
    `  blockquote { border-left: 4px solid ${C.accent}; font-size: 26px; font-style: italic; padding-left: 24px; }`,
    `  footer { color: ${C.muted}; font-size: 12px; }`,
    `footer: "${(outline.footer || "").replace(/"/g, '\\"')}"`,
    "---",
    "",
  ].join("\n");
}

function slideMd(d) {
  switch (d.type) {
    case "cover":
      return [
        "<!-- _paginate: false -->",
        "<!-- _footer: '' -->",
        "",
        `# ${d.title}`,
        "",
        d.subtitle ? `## ${d.subtitle}` : "",
        "",
        d.footer ? `<small style="color:${C.accent}">${d.footer}</small>` : "",
      ].filter(Boolean).join("\n");

    case "section":
      return [
        "<!-- _class: section -->",
        "<!-- _paginate: false -->",
        "",
        `# ${d.title}`,
      ].join("\n");

    case "bullets":
      return [
        `# ${d.title}`,
        "",
        ...(d.bullets || []).slice(0, 6).map((b) => `- ${b}`),
      ].join("\n");

    case "two-column":
      return [
        `# ${d.title}`,
        "",
        `<div style="display:grid;grid-template-columns:1fr 1fr;gap:40px;">`,
        `<div><h2>${d.left.heading}</h2><ul>${(d.left.items || []).slice(0, 6).map((i) => `<li>${i}</li>`).join("")}</ul></div>`,
        `<div><h2>${d.right.heading}</h2><ul>${(d.right.items || []).slice(0, 6).map((i) => `<li>${i}</li>`).join("")}</ul></div>`,
        `</div>`,
      ].join("\n");

    case "stat":
      return [
        "<!-- _class: stat -->",
        "",
        `<div class="stat-value">${d.value}</div>`,
        `<div class="stat-caption">${d.caption}</div>`,
      ].join("\n");

    case "quote":
      return [
        "",
        `> ${d.quote}`,
        "",
        d.attribution ? `<small style="color:${C.muted}">— ${d.attribution}</small>` : "",
      ].filter(Boolean).join("\n");

    case "code":
      return [
        `# ${d.title}`,
        "",
        `\`\`\`${d.language || ""}`,
        d.code,
        "```",
      ].join("\n");

    case "image":
      return [
        `# ${d.title}`,
        "",
        `![w:900](${d.path})`,
        "",
        d.caption ? `<small><em>${d.caption}</em></small>` : "",
      ].filter(Boolean).join("\n");

    case "agenda":
      return [
        `# ${d.title || "Agenda"}`,
        "",
        ...(d.items || []).map((it, i) => `${i + 1}. ${it}`),
      ].join("\n");

    case "closing":
      return [
        "<!-- _paginate: false -->",
        "",
        `# ${d.title || "Thank you."}`,
        "",
        d.subtitle ? d.subtitle : "",
      ].filter(Boolean).join("\n");

    default:
      throw new Error(`unknown slide type: ${d.type}`);
  }
}

const body = outline.slides.map(slideMd).join("\n\n---\n\n");
fs.writeFileSync(outPath, frontMatter() + body + "\n");
console.error(`wrote ${outPath} (${outline.slides.length} slides)`);
