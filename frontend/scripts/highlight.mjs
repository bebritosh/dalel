// Bonus: capture the claim screen with a receipt line highlighted (mock mode).
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUT = resolve(__dirname, "..", "screenshots");
const BASE = process.env.BASE ?? "http://localhost:5173";

const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await ctx.newPage();

await page.addInitScript(() => sessionStorage.setItem("case:1", "mock"));
await page.goto(`${BASE}/case/1/review?token=mock`);
await page.getByText("Поля из чека").first().waitFor();
for (let i = 0; i < 6; i++) {
  const btn = page.getByRole("button", { name: "Подтвердить" }).first();
  if ((await btn.count()) === 0) break;
  await btn.click();
  await page.waitForTimeout(250);
}
await page.getByRole("button", { name: "Перейти к претензии" }).click();
await page.waitForURL("**/claim");
await page.getByRole("button", { name: "Скачать DOCX" }).waitFor();
// Click the amount token to highlight its receipt line.
await page.getByRole("button", { name: /249 990,00/ }).first().click();
await page.waitForTimeout(700);
await page.screenshot({ path: resolve(OUT, "claim-highlight-1440x900.png"), fullPage: true });
console.log("shot claim-highlight-1440x900");
await browser.close();
