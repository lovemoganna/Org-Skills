const fs = require('node:fs');
const path = require('node:path');
const http = require('node:http');
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
const jsFile = path.resolve(__dirname, '../scripts/sql_ui.js');
const uiJS = fs.readFileSync(jsFile, 'utf8');
const fixed = "SELECT * FROM read_xlsx('https://docs.google.com/spreadsheets/d/id/export?format=xlsx', sheet = 'users', header = true)";
const dynamic = 'select uid,amount from fiat_transactions where amount>1 order by uid;';
const pageHTML = '<!doctype html><html><meta charset="utf-8"><title>SQL UI Test</title>' +
  '<style>.sql-keyword{color:#2765af}.sql-string{color:#5e852a}.sql-comment{color:#777}pre{white-space:pre}</style>' +
  '<div id="static"></div><div id="dynamic"></div><script src="/sql_ui.js"></script>' +
  '<script>window.staticSql=' + JSON.stringify(fixed) + ';window.dynamicSql=' + JSON.stringify(dynamic) + ';' +
  'window.s=OntologySQL.renderSqlBlock(document.querySelector("#static"),window.staticSql);' +
  'window.d=OntologySQL.renderSqlBlock(document.querySelector("#dynamic"),window.dynamicSql);</script></html>';
(async () => {
  const server = http.createServer((req, res) => {
    const body = req.url === '/sql_ui.js' ? uiJS : pageHTML;
    res.setHeader('Content-Type', req.url === '/sql_ui.js' ? 'application/javascript' : 'text/html; charset=utf-8');
    res.end(body);
  });
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  let browser;
  try {
    const port = server.address().port;
    const origin = 'http://127.0.0.1:' + port;
    browser = await chromium.launch({headless:true, args:['--no-sandbox']});
    const context = await browser.newContext({ permissions:['clipboard-read','clipboard-write'] });
    const page = await context.newPage();
    await page.goto(origin, {waitUntil:'load'});
    const result = await page.evaluate(() => ({
      origin: location.origin,
      static: window.s.formatted,
      dynamic: window.d.formatted,
      highlighted: document.querySelectorAll('.sql-keyword').length,
      scripts: document.querySelectorAll('script[src^="http"]').length,
    }));
    assert.equal(result.origin, origin);
    assert.ok(result.highlighted > 0);
    assert.ok(result.dynamic.includes('\nFROM ') && result.dynamic.includes('\nWHERE '));
    assert.ok(result.static.includes('\n  sheet ='));
    assert.equal(result.scripts,0);
    await page.locator('#dynamic button').click();
    const copied = await page.evaluate(async () => navigator.clipboard.readText());
    assert.equal(copied,result.dynamic);
    assert.ok(!copied.includes('<span') && !copied.includes('sql-keyword'));
    console.log(JSON.stringify({status:'PASS',origin,formatting:true,highlighting:true,
      static_and_dynamic:true,native_clipboard:true,html_self_contained_no_cdn:true},null,2));
    await context.close();
  } finally {
    if (browser) await browser.close();
    await new Promise(resolve=>server.close(resolve));
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
