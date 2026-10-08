const fs = require('node:fs');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');

const file = 'ontology-analysis.html';
assert.ok(fs.existsSync(file), 'CI must download the CURRENT real SQL report artifact');
const report = fs.readFileSync(file, 'utf8');
assert.ok(report.length > 10000);
assert.ok(!/(<script[^>]+src=|<link[^>]+href=["']https?:\/\/)/i.test(report), 'external code or CSS found');
(async () => {
  const server = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'text/html; charset=utf-8');
    res.end(report);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    browser = await chromium.launch({ headless: true, args: ['--no-sandbox'] });
    for (const [label, width, height] of [['desktop', 1366, 860], ['mobile', 390, 844]]) {
      const context = await browser.newContext({
        viewport: {width,height}, permissions: ['clipboard-read','clipboard-write']
      });
      const page = await context.newPage();
      const errors = [];
      page.on('pageerror', error => errors.push(error.message));
      const origin = 'http://127.0.0.1:' + server.address().port;
      const response = await page.goto(origin, {waitUntil:'load'});
      assert.equal(response.status(), 200);
      assert.equal(await page.locator('h1').count(), 1);
      assert.equal(await page.locator('.sql-shell').count(), 7, 'all seven actual SQL blocks rendered');
      assert.equal(await page.locator('.sql-shell .sql-keyword').count() > 0, true);
      assert.equal(await page.locator('details').count(), 7);
      const before = await page.evaluate(() => document.documentElement.scrollWidth);
      if (before > width+2) {
        const overflowers = await page.evaluate(() =>
          [...document.querySelectorAll('body *')].filter(e => {
            const rect = e.getBoundingClientRect();
            return rect.right > innerWidth + 3 && rect.width > 0;
          }).slice(0, 25).map(e => ({
            tag:e.tagName, cls:e.className, width:Math.round(e.getBoundingClientRect().width),
            right:Math.round(e.getBoundingClientRect().right),
            overflow:getComputedStyle(e).overflowX,
            text:(e.textContent || '').trim().slice(0,50)
          })));
        console.error('HORIZONTAL_OVERFLOW_ELEMENTS',JSON.stringify(overflowers));
      }
      assert.ok(before <= width+2, 'mobile/desktop horizontal document overflow: '+before+' > '+width);
      await page.locator('details').first().locator('summary').click();
      const beforeCopy = await page.locator('details').first().locator('.sql-toolbar button').textContent();
      assert.ok(beforeCopy.includes('复制 SQL'));
      await page.locator('details').first().locator('.sql-toolbar button').click();
      const copied = await page.evaluate(async () => navigator.clipboard.readText());
      assert.ok(copied.length > 100 && copied.includes('SELECT'));
      assert.ok(!copied.includes('<span') && !copied.includes('sql-keyword'));
      assert.ok((await page.locator('details').first().locator('.sql-toolbar button').textContent()).includes('已复制'));
      assert.deepEqual(errors, []);
      console.log(JSON.stringify({status:'PASS',viewport:label,origin,
        sqlRendered:7,clipboardBytes:copied.length,documentWidth:before,
        actualReport:true}));
      await context.close();
    }
  } finally {
    if(browser) await browser.close();
    await new Promise(resolve => server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
