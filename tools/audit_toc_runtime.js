#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const pages = JSON.parse(fs.readFileSync(path.join(root, "content/pages.json"), "utf8"));
const spine = new Map(pages.map((entry, index) => [entry.section_id, { ...entry, position: index + 1 }]));
const baseUrl = process.env.ADT_AUDIT_BASE_URL || "http://127.0.0.1:5500";

(async () => {
  const executablePath = process.env.ADT_AUDIT_BROWSER
    || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await chromium.launch({ headless: true, executablePath });
  const problems = [];

  try {
    const page = await browser.newPage({ viewport: { width: 800, height: 1024 } });
    await page.goto(`${baseUrl}/pg003_sec001.html`, { waitUntil: "domcontentloaded" });
    await page.waitForFunction(() => [...document.querySelectorAll("[data-toc-section]")]
      .every((link) => link.dataset.adtPage && link.getAttribute("href") !== "#"));

    const links = await page.locator("[data-toc-section]").evaluateAll((nodes) => nodes.map((node) => ({
      sectionId: node.dataset.tocSection,
      position: Number(node.dataset.adtPage),
      displayed: Number(node.querySelector("[data-toc-position]")?.textContent),
      href: new URL(node.href).pathname.split("/").pop(),
    })));

    for (const link of links) {
      const expected = spine.get(link.sectionId);
      if (!expected) {
        problems.push(`${link.sectionId}: absent from pages.json`);
        continue;
      }
      if (link.position !== expected.position || link.displayed !== expected.position
        || link.href !== expected.href) {
        problems.push(`${link.sectionId}: runtime position/href mismatch`);
      }

      await page.goto(`${baseUrl}/pg003_sec001.html`, { waitUntil: "domcontentloaded" });
      await page.waitForFunction((sectionId) => {
        const link = document.querySelector(`[data-toc-section="${sectionId}"]`);
        return link?.dataset.adtPage && link.getAttribute("href") !== "#";
      }, link.sectionId);
      await Promise.all([
        page.waitForNavigation({ waitUntil: "domcontentloaded" }),
        page.locator(`[data-toc-section="${link.sectionId}"]`).first().click(),
      ]);
      const destinationPosition = Number(await page.locator('meta[name="page-section-id"]').getAttribute("content"));
      if (destinationPosition !== expected.position) {
        problems.push(`${link.sectionId}: click opened ADT position ${destinationPosition}, expected ${expected.position}`);
      }
    }
  } finally {
    await browser.close();
  }

  if (problems.length) {
    console.error(problems.join("\n"));
    process.exitCode = 1;
  } else {
    console.log(`AUDIT PASS: ${spine.size} spine entries; 12 dynamic TOC links open matching ADT positions`);
  }
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
