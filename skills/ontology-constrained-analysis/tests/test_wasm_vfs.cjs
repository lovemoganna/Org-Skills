const fs=require('node:fs');
const path=require('node:path');
const http=require('node:http');
const {chromium}=require('playwright');
const allowed=new Set(['/','/duckdb.bundle.mjs','/duckdb-browser-eh.worker.js','/duckdb-eh.wasm','/source.xlsx','/source-receipt.json']);
const paths={'/':'skills/ontology-constrained-analysis/tests/wasm_probe.html'};
const mime={'.html':'text/html; charset=utf-8','.mjs':'application/javascript','.js':'application/javascript','.wasm':'application/wasm','.xlsx':'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet','.json':'application/json'};
(async()=>{
 const server=http.createServer((req,res)=>{
  if(!allowed.has(req.url)){res.writeHead(404);res.end();return}
  const name=paths[req.url]||req.url.slice(1);
  try{const bytes=fs.readFileSync(name);res.writeHead(200,{'Content-Type':mime[path.extname(name)]||'application/octet-stream','Content-Length':bytes.length});res.end(bytes)}
  catch(e){res.writeHead(500);res.end(String(e))}
 });
 await new Promise(done=>server.listen(0,'127.0.0.1',done));
 let browser;let result;
 try{
  const origin='http://127.0.0.1:'+server.address().port;
  browser=await chromium.launch({headless:true,args:['--no-sandbox']});
  const page=await browser.newPage();
  page.on('console',m=>{if(m.type()==='error')console.error('browser console:',m.text())});
  await page.goto(origin,{waitUntil:'domcontentloaded'});
  await page.waitForFunction('window.__ontologyProbe !== undefined',null,{timeout:150000});
  result=await page.evaluate('window.__ontologyProbe');
  fs.writeFileSync('wasm-runtime-receipt.json',JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify(result,null,2));
  // Each capability must have its own verdict; success in one cannot mask failure in another.
  const range=result.remote_fetch?.range;
  if(result.remote_fetch?.range_capability==='PARTIAL_CONTENT_CONFIRMED' &&
     !(range?.status===206 && range?.bytes===32 && /^bytes 0-31\/\d+$/.test(range.content_range||''))) {
    throw new Error('RANGE_FALSE_PASS');
  }
  if(!['PARTIAL_CONTENT_CONFIRMED','NOT_CONFIRMED'].includes(result.remote_fetch?.range_capability)) {
    throw new Error('RANGE_PROBE_NOT_CLASSIFIED');
  }
  if(!['PASS','BLOCKED'].includes(result.fixed_url_sql?.status)){
    throw new Error('FIXED_REMOTE_SQL_UNVERIFIED_OR_INCONSISTENT');
  }
  if(result.fixed_url_sql.status==='PASS' &&
     String(result.fixed_url_sql.row_count)!==String(result.sheets?.users?.row_count)) {
    throw new Error('FIXED_REMOTE_SQL_ROW_COUNT_MISMATCH');
  }
  console.log('CAPABILITY_VERDICTS',JSON.stringify({
    exact_remote_sql:result.fixed_url_sql.status,
    range:result.remote_fetch.range_capability,
    vfs:result.status
  }));
  if(result.status!=='VFS_READ_XLSX_PASS')process.exitCode=1;
 }finally{
  if(browser)await browser.close();
  await new Promise(done=>server.close(done));
 }
})().catch(err=>{console.error(err);process.exitCode=1;});
