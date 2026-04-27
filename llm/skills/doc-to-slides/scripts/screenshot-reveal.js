#!/usr/bin/env node
// screenshot-reveal.js — Stage 4b for Reveal.js decks.
// Boots a headless browser, navigates each slide, and writes JPEGs.
// usage: node screenshot-reveal.js <deck.html> <out-dir>

const path = require("path");
const fs = require("fs");

(async () => {
  const [, , htmlPath, outDir] = process.argv;
  if (!htmlPath || !outDir) {
    console.error("usage: screenshot-reveal.js <deck.html> <out-dir>");
    process.exit(64);
  }
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  let chromium;
  try {
    ({ chromium } = require("playwright"));
  } catch (e) {
    console.error("error: playwright not installed. Run: npm i -D playwright && npx playwright install chromium");
    process.exit(69);
  }

  const fileUrl = "file://" + path.resolve(htmlPath);
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 2 });
  const page = await ctx.newPage();
  await page.goto(fileUrl, { waitUntil: "networkidle" });
  await page.waitForFunction(() => window.Reveal && Reveal.isReady && Reveal.isReady());

  const total = await page.evaluate(() => Reveal.getTotalSlides());
  console.error(`capturing ${total} slides → ${outDir}`);

  for (let i = 0; i < total; i++) {
    await page.evaluate((idx) => Reveal.slide(idx, 0, 0), i);
    await page.waitForTimeout(150); // let transitions settle
    const file = path.join(outDir, `s-${String(i + 1).padStart(2, "0")}.jpg`);
    await page.screenshot({ path: file, type: "jpeg", quality: 85, fullPage: false });
  }

  await browser.close();
  console.error("done");
})();
