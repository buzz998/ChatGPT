import { chromium } from 'playwright-core';
const b = await chromium.launch({ executablePath: process.env.PLAYWRIGHT_CHROME });
const p = await b.newPage({ viewport: { width: 2000, height: 1000 } });
await p.goto('file://' + process.argv[2]);
await p.evaluate(() => document.fonts.ready);
await p.waitForTimeout(500);
await p.screenshot({ path: process.argv[3], fullPage: true, type: 'jpeg', quality: 88 });
await b.close();
