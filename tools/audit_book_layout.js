#!/usr/bin/env node

const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const root = path.resolve(__dirname, "..");
const pages = JSON.parse(fs.readFileSync(path.join(root, "content/pages.json"), "utf8"));
const allViewports = [
  { name: "desktop", width: 1280, height: 800 },
  { name: "tablet", width: 800, height: 1024 },
  { name: "phone", width: 390, height: 844 },
];
const requestedViewports = new Set((process.env.ADT_AUDIT_VIEWPORTS || "")
  .split(",")
  .map((name) => name.trim())
  .filter(Boolean));
const viewports = requestedViewports.size
  ? allViewports.filter((viewport) => requestedViewports.has(viewport.name))
  : allViewports;

const baseUrl = process.env.ADT_AUDIT_BASE_URL || "http://127.0.0.1:5500";

(async () => {
  const executablePath = process.env.ADT_AUDIT_BROWSER
    || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  const browser = await chromium.launch({ headless: true, executablePath });
  const results = [];

  try {
    for (const viewport of viewports) {
      const context = await browser.newContext({ viewport });
      const page = await context.newPage();

      for (const entry of pages) {
        await page.goto(`${baseUrl}/${entry.href}`, { waitUntil: "domcontentloaded" });
        await page.waitForFunction(() => getComputedStyle(document.querySelector("#content")).opacity === "1");

        results.push(await page.evaluate(({ id, viewportName }) => {
          const content = document.querySelector("#content");
          const section = content?.querySelector(":scope > section");
          const contentRect = content?.getBoundingClientRect();
          const sectionRect = section?.getBoundingClientRect();
          const viewportWidth = document.documentElement.clientWidth;
          const main = document.querySelector("main");
          const dockHeight = Math.max(0, ...[...document.querySelectorAll("#nav-container *")]
            .filter((element) => {
              const rect = element.getBoundingClientRect();
              return getComputedStyle(element).position === "fixed"
                && rect.height > 0
                && rect.height <= 200
                && rect.bottom >= innerHeight - 2;
            })
            .map((element) => element.getBoundingClientRect().height));
          const visibleText = [...document.querySelectorAll("#content p, #content li, #content td, #content th, #content label")]
            .filter((element) => {
              const rect = element.getBoundingClientRect();
              const style = getComputedStyle(element);
              return rect.width > 0 && rect.height > 0 && style.display !== "none" && style.visibility !== "hidden";
            });
          const fontSizes = visibleText.map((element) => Number.parseFloat(getComputedStyle(element).fontSize));

          const contentBottomMargin = content
            ? Number.parseFloat(getComputedStyle(content).marginBottom)
            : 0;
          const mainBottomPadding = main
            ? Number.parseFloat(getComputedStyle(main).paddingBottom)
            : 0;
          const highlightProbe = document.createElement("span");
          highlightProbe.dataset.wordIndex = "audit";
          highlightProbe.className = "bg-yellow-300";
          highlightProbe.textContent = "audit";
          content?.appendChild(highlightProbe);
          const highlightStyle = getComputedStyle(highlightProbe);
          const highlightPass = highlightStyle.backgroundColor === "rgb(253, 224, 71)"
            && [highlightStyle.borderTopWidth, highlightStyle.borderRightWidth,
              highlightStyle.borderBottomWidth, highlightStyle.borderLeftWidth]
              .every((width) => Number.parseFloat(width) === 0);
          highlightProbe.remove();

          return {
            id,
            viewport: viewportName,
            overflow: document.documentElement.scrollWidth > viewportWidth + 1,
            contentDelta: contentRect ? contentRect.left + contentRect.width / 2 - viewportWidth / 2 : null,
            sectionDelta: sectionRect ? sectionRect.left + sectionRect.width / 2 - viewportWidth / 2 : null,
            minFont: fontSizes.length ? Math.min(...fontSizes) : null,
            navigationClearance: Math.max(mainBottomPadding, contentBottomMargin),
            dockHeight,
            highlightPass,
            controls: document.querySelectorAll("#content input, #content textarea, #content button, #content [data-activity-item]").length,
            semanticText: (content?.innerText || "").trim().length,
          };
        }, { id: entry.section_id, viewportName: viewport.name }));
      }

      await context.close();
    }
  } finally {
    await browser.close();
  }

  const summary = {
    pages: pages.length,
    checks: results.length,
    overflow: results.filter((row) => row.overflow),
    offCentreContent: results.filter((row) => Math.abs(row.contentDelta || 0) > 2),
    offCentreSections: results.filter((row) => Math.abs(row.sectionDelta || 0) > 2),
    unreadableText: results.filter((row) => row.minFont !== null && row.minFont < 14),
    unsafeNavigationClearance: results.filter((row) => row.dockHeight > row.navigationClearance + 1),
    highlightFailures: results.filter((row) => !row.highlightPass),
    missingSemanticText: results.filter((row) => row.semanticText === 0),
    interactivePages: [...new Set(results.filter((row) => row.controls > 0).map((row) => row.id))],
  };

  process.stdout.write(`${JSON.stringify(summary, null, 2)}\n`);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
