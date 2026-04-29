#!/usr/bin/env node
// render-pptx.js — outline JSON → PPTX via pptxgenjs.
// usage: node render-pptx.js <outline.json> <out.pptx> [theme.json]

const fs = require("fs");
const path = require("path");
const PptxGenJS = require("pptxgenjs");

const [, , outlinePath, outPath, themePath] = process.argv;
if (!outlinePath || !outPath) {
  console.error("usage: render-pptx.js <outline.json> <out.pptx> [theme.json]");
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
const F = theme.fonts;
const W = 13.333, H = 7.5;
const MARGIN = 0.55;

const pres = new PptxGenJS();
pres.layout = "LAYOUT_WIDE";
pres.defineLayout({ name: "LAYOUT_WIDE", width: W, height: H });

const TOTAL = outline.slides.length;
let pageNum = 0;

function footer(s) {
  pageNum += 1;
  if (pageNum === 1) return; // no footer on cover
  s.addText(outline.footer || "", {
    x: MARGIN, y: H - 0.4, w: W - 2.0, h: 0.25,
    fontSize: 9, fontFace: F.body, color: C.muted,
  });
  s.addText(`${pageNum} / ${TOTAL}`, {
    x: W - MARGIN - 0.8, y: H - 0.4, w: 0.8, h: 0.25,
    fontSize: 9, fontFace: F.body, color: C.muted, align: "right",
  });
}

function title(s, text, y = MARGIN, h = 1.0, size = 32) {
  s.addText(text, {
    x: MARGIN, y, w: W - 2 * MARGIN, h,
    fontSize: size, fontFace: F.heading, bold: true, color: C.text,
  });
}

function bg(s, color = C.bg) {
  s.background = { color };
}

// --- slide-type renderers ---
const renderers = {
  cover(s, d) {
    bg(s);
    s.addText(d.title, {
      x: MARGIN, y: 2.2, w: W - 2 * MARGIN, h: 2.0,
      fontSize: 56, fontFace: F.heading, bold: true, color: C.text,
    });
    if (d.subtitle) {
      s.addText(d.subtitle, {
        x: MARGIN, y: 4.3, w: W - 2 * MARGIN, h: 0.7,
        fontSize: 20, fontFace: F.body, color: C.muted,
      });
    }
    if (d.footer) {
      s.addText(d.footer, {
        x: MARGIN, y: H - 0.7, w: W - 2 * MARGIN, h: 0.3,
        fontSize: 11, fontFace: F.body, color: C.accent,
      });
    }
  },

  section(s, d) {
    bg(s, C.accent);
    s.addText(d.title, {
      x: MARGIN, y: 3.0, w: W - 2 * MARGIN, h: 1.5,
      fontSize: 44, fontFace: F.heading, bold: true, color: C.bg, align: "center",
    });
  },

  bullets(s, d) {
    bg(s);
    title(s, d.title);
    const bullets = (d.bullets || []).slice(0, 6);
    s.addText(
      bullets.map((b) => ({ text: b, options: { bullet: { indent: 18 } } })),
      {
        x: MARGIN, y: 1.7, w: W - 2 * MARGIN, h: H - 2.6,
        fontSize: 18, fontFace: F.body, color: C.text, paraSpaceAfter: 8,
      }
    );
  },

  "two-column"(s, d) {
    bg(s);
    title(s, d.title);
    const colW = (W - 3 * MARGIN) / 2;
    [
      { side: d.left, x: MARGIN },
      { side: d.right, x: MARGIN * 2 + colW },
    ].forEach(({ side, x }) => {
      s.addText(side.heading, {
        x, y: 1.7, w: colW, h: 0.5,
        fontSize: 18, fontFace: F.heading, bold: true, color: C.accent,
      });
      s.addText(
        (side.items || []).slice(0, 6).map((b) => ({ text: b, options: { bullet: { indent: 16 } } })),
        { x, y: 2.3, w: colW, h: H - 3.2, fontSize: 16, fontFace: F.body, color: C.text, paraSpaceAfter: 6 }
      );
    });
  },

  stat(s, d) {
    bg(s);
    s.addText(d.value, {
      x: MARGIN, y: 2.0, w: W - 2 * MARGIN, h: 2.5,
      fontSize: 140, fontFace: F.heading, bold: true, color: C.accent, align: "center",
    });
    s.addText(d.caption, {
      x: MARGIN, y: 4.7, w: W - 2 * MARGIN, h: 0.8,
      fontSize: 22, fontFace: F.body, color: C.text, align: "center",
    });
  },

  quote(s, d) {
    bg(s);
    s.addText(`"${d.quote}"`, {
      x: MARGIN + 0.5, y: 2.2, w: W - 2 * MARGIN - 1.0, h: 2.5,
      fontSize: 30, fontFace: F.heading, italic: true, color: C.text,
    });
    if (d.attribution) {
      s.addText(`— ${d.attribution}`, {
        x: MARGIN + 0.5, y: 4.9, w: W - 2 * MARGIN - 1.0, h: 0.5,
        fontSize: 16, fontFace: F.body, color: C.muted,
      });
    }
  },

  code(s, d) {
    bg(s);
    title(s, d.title, MARGIN, 0.7, 24);
    s.addShape("rect", {
      x: MARGIN, y: 1.4, w: W - 2 * MARGIN, h: H - 2.3,
      fill: { color: C.surface }, line: { color: C.border, width: 0.5 },
    });
    s.addText(d.code, {
      x: MARGIN + 0.2, y: 1.55, w: W - 2 * MARGIN - 0.4, h: H - 2.6,
      fontSize: 14, fontFace: F.mono, color: C.text, valign: "top",
    });
  },

  image(s, d) {
    bg(s);
    title(s, d.title, MARGIN, 0.7, 24);
    s.addImage({ path: d.path, x: MARGIN + 1.0, y: 1.6, w: W - 2 * MARGIN - 2.0, h: H - 3.0, sizing: { type: "contain", w: W - 2 * MARGIN - 2.0, h: H - 3.0 } });
    if (d.caption) {
      s.addText(d.caption, {
        x: MARGIN, y: H - 1.1, w: W - 2 * MARGIN, h: 0.4,
        fontSize: 12, fontFace: F.body, italic: true, color: C.muted, align: "center",
      });
    }
  },

  agenda(s, d) {
    bg(s);
    title(s, d.title || "Agenda");
    s.addText(
      (d.items || []).map((it, i) => ({
        text: `${i + 1}. ${it}`,
        options: { paraSpaceAfter: 12 },
      })),
      { x: MARGIN + 0.5, y: 1.8, w: W - 2 * MARGIN - 1.0, h: H - 2.6, fontSize: 22, fontFace: F.body, color: C.text }
    );
  },

  "center-panel"(s, d) {
    bg(s);
    const ct = d.center || {};
    title(s, d.title, MARGIN, 0.7, 24);

    if (d.layout === "sides") {
      const panelW = 3.0, panelY = 1.5, panelH = 5.2;
      const gap = 0.35;
      const ctX = MARGIN + panelW + gap;
      const ctW = W - 2 * MARGIN - 2 * panelW - 2 * gap;

      [d.left, d.right].forEach((panel, i) => {
        if (!panel) return;
        const px = i === 0 ? MARGIN : W - MARGIN - panelW;
        s.addText(panel.heading, {
          x: px, y: panelY, w: panelW, h: 0.4,
          fontSize: 16, fontFace: F.heading, bold: true, color: C.accent,
        });
        s.addText(
          (panel.bullets || []).slice(0, 4).map((b) => ({ text: b, options: { bullet: { indent: 14 } } })),
          { x: px, y: panelY + 0.55, w: panelW, h: panelH - 0.65, fontSize: 12, fontFace: F.body, color: C.text, paraSpaceAfter: 6 }
        );
      });

      if (ct.kind === "text") {
        s.addText(ct.value || "", {
          x: ctX, y: panelY + 0.5, w: ctW, h: panelH - 0.5,
          fontSize: 48, fontFace: F.heading, bold: true, color: C.accent, align: "center", valign: "middle",
        });
      } else if (ct.kind === "code") {
        s.addShape("rect", {
          x: ctX, y: panelY, w: ctW, h: panelH,
          fill: { color: C.surface }, line: { color: C.border, width: 0.5 },
        });
        s.addText(ct.code || "", {
          x: ctX + 0.15, y: panelY + 0.15, w: ctW - 0.3, h: panelH - 0.3,
          fontSize: 11, fontFace: F.mono, color: C.text, valign: "top",
        });
      } else if (ct.kind === "table") {
        const hdr = (ct.headers || []).map((h) => ({ text: h, options: { bold: true, fill: { color: C.surface }, fontSize: 11 } }));
        const dataRows = (ct.rows || []).map((row) => row.map((cell) => ({ text: cell, options: { fontSize: 10 } })));
        s.addTable([hdr, ...dataRows], {
          x: ctX, y: panelY + 0.3, w: ctW,
          border: { type: "solid", pt: 0.5, color: C.border },
          colW: ct.headers ? ct.headers.map(() => ctW / ct.headers.length) : undefined,
          fontFace: F.body, autoPage: false,
        });
      }
    } else if (d.layout === "corners") {
      const cornerW = 2.9, cornerH = 2.3;
      const gapC = 0.35;
      const ctX = MARGIN + cornerW + gapC;
      const ctW = W - 2 * MARGIN - 2 * cornerW - 2 * gapC;
      const ctY = 1.5, ctH = 5.2;

      const corners = [
        { key: "top_left", x: MARGIN, y: 1.5 },
        { key: "top_right", x: W - MARGIN - cornerW, y: 1.5 },
        { key: "bottom_left", x: MARGIN, y: 4.2 },
        { key: "bottom_right", x: W - MARGIN - cornerW, y: 4.2 },
      ];
      corners.forEach(({ key, x, y }) => {
        const panel = d[key];
        if (!panel) return;
        s.addText(panel.heading, {
          x, y, w: cornerW, h: 0.35,
          fontSize: 14, fontFace: F.heading, bold: true, color: C.accent,
        });
        s.addText(
          (panel.bullets || []).slice(0, 3).map((b) => ({ text: b, options: { bullet: { indent: 12 } } })),
          { x, y: y + 0.55, w: cornerW, h: cornerH - 0.65, fontSize: 11, fontFace: F.body, color: C.text, paraSpaceAfter: 5 }
        );
      });

      if (ct.kind === "text") {
        s.addText(ct.value || "", {
          x: ctX, y: ctY + 0.5, w: ctW, h: ctH - 1.0,
          fontSize: 64, fontFace: F.heading, bold: true, color: C.accent, align: "center", valign: "middle",
        });
      } else if (ct.kind === "code") {
        s.addShape("rect", {
          x: ctX, y: ctY + 0.2, w: ctW, h: ctH - 0.4,
          fill: { color: C.surface }, line: { color: C.border, width: 0.5 },
        });
        s.addText(ct.code || "", {
          x: ctX + 0.15, y: ctY + 0.35, w: ctW - 0.3, h: ctH - 0.7,
          fontSize: 10, fontFace: F.mono, color: C.text, valign: "top",
        });
      } else if (ct.kind === "table") {
        const hdr = (ct.headers || []).map((h) => ({ text: h, options: { bold: true, fill: { color: C.surface }, fontSize: 11 } }));
        const dataRows = (ct.rows || []).map((row) => row.map((cell) => ({ text: cell, options: { fontSize: 10 } })));
        s.addTable([hdr, ...dataRows], {
          x: ctX + 0.1, y: ctY + 0.5, w: ctW - 0.2,
          border: { type: "solid", pt: 0.5, color: C.border },
          colW: ct.headers ? ct.headers.map(() => (ctW - 0.2) / ct.headers.length) : undefined,
          fontFace: F.body, autoPage: false,
        });
      }
    }
  },

  closing(s, d) {
    bg(s);
    s.addText(d.title || "Thank you.", {
      x: MARGIN, y: 2.5, w: W - 2 * MARGIN, h: 1.5,
      fontSize: 56, fontFace: F.heading, bold: true, color: C.text,
    });
    if (d.subtitle) {
      s.addText(d.subtitle, {
        x: MARGIN, y: 4.2, w: W - 2 * MARGIN, h: 0.8,
        fontSize: 22, fontFace: F.body, color: C.muted,
      });
    }
  },
};

for (const slideDef of outline.slides) {
  const s = pres.addSlide();
  const r = renderers[slideDef.type];
  if (!r) {
    console.error(`error: unknown slide type "${slideDef.type}"`);
    process.exit(65);
  }
  r(s, slideDef);
  if (slideDef.type !== "cover" && slideDef.type !== "section" && slideDef.type !== "closing") footer(s);
  else pageNum += 1;
}

pres.writeFile({ fileName: outPath }).then(() => {
  console.error(`wrote ${outPath} (${TOTAL} slides)`);
});
