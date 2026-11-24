// Playwright screenshots of the three screens at 1440x900 and 390x844.
// Usage:
//   SHOT_MODE=mock BASE=http://localhost:5173 node scripts/screenshots.mjs
//   SHOT_MODE=http BASE=http://localhost:5173 node scripts/screenshots.mjs
// In http mode a backend must be running and the demo files must exist at
// ../eval/cases/demo-001/.

import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { mkdirSync } from "node:fs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, "..", "screenshots");
const BASE = process.env.BASE ?? "http://localhost:5173";
const MODE = process.env.SHOT_MODE ?? "mock";
const PREFIX = process.env.PREFIX ?? "";
const DEMO = resolve(__dirname, "..", "..", "eval", "cases", "demo-001");

const VIEWPORTS = [
  { name: "1440x900", width: 1440, height: 900 },
  { name: "390x844", width: 390, height: 844 },
];

mkdirSync(OUT, { recursive: true });

async function shot(page, name) {
  await page.waitForTimeout(600);
  await page.screenshot({ path: resolve(OUT, `${PREFIX}${name}.png`), fullPage: true });
  console.log("shot", `${PREFIX}${name}`);
}

async function waitText(page, text, timeout = 15000) {
  await page.getByText(text, { exact: false }).first().waitFor({ timeout });
}

async function waitClaimReady(page) {
  // Either the download button (success) or the blocked block appears.
  await Promise.race([
    page.getByRole("button", { name: "Скачать DOCX" }).waitFor({ timeout: 15000 }),
    page.getByText("Экспорт заблокирован").waitFor({ timeout: 15000 }),
  ]);
}

async function confirmAll(page) {
  await page.waitForTimeout(400);
  // Click every "Подтвердить" button, re-querying as the list changes.
  for (let i = 0; i < 6; i++) {
    const btn = page.getByRole("button", { name: "Подтвердить" }).first();
    if ((await btn.count()) === 0) break;
    await btn.click();
    await page.waitForTimeout(250);
  }
}

async function runMock(browser) {
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await ctx.newPage();

    await page.goto(`${BASE}/`);
    await waitText(page, "Новое дело");
    await shot(page, `upload-${vp.name}`);

    await page.addInitScript(() => sessionStorage.setItem("case:1", "mock"));
    await page.goto(`${BASE}/case/1/review?token=mock`);
    await waitText(page, "Поля из чека");
    await shot(page, `review-${vp.name}`);

    await confirmAll(page);
    await page.getByRole("button", { name: "Перейти к претензии" }).click();
    await page.waitForURL("**/claim");
    await waitClaimReady(page);
    await shot(page, `claim-${vp.name}`);

    await ctx.close();
  }
}

async function runHttp(browser) {
  for (const vp of VIEWPORTS) {
    const ctx = await browser.newContext({ viewport: { width: vp.width, height: vp.height } });
    const page = await ctx.newPage();

    await page.goto(`${BASE}/`);
    await waitText(page, "Новое дело");
    await page.setInputFiles('input[type="file"]', [
      resolve(DEMO, "receipt.png"),
      resolve(DEMO, "chat.txt"),
    ]);
    await page.waitForTimeout(300);
    await shot(page, `http-upload-${vp.name}`);

    await page.getByRole("button", { name: "Разобрать" }).click();
    await page.waitForURL("**/review", { timeout: 20000 });
    await waitText(page, "Поля из чека");
    await shot(page, `http-review-${vp.name}`);

    await confirmAll(page);
    await page.getByRole("button", { name: "Перейти к претензии" }).click();
    await page.waitForURL("**/claim");
    await waitClaimReady(page);
    await shot(page, `http-claim-${vp.name}`);

    await ctx.close();
  }
}

const browser = await chromium.launch();
if (MODE === "http") await runHttp(browser);
else await runMock(browser);
await browser.close();
console.log("done", MODE);
