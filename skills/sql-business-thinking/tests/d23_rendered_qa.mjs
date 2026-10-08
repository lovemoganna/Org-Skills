import assert from 'node:assert/strict';
import {readFileSync, mkdirSync, writeFileSync} from 'node:fs';
import {join} from 'node:path';
import puppeteer from 'puppeteer-core';

const reportPath = 'skills/sql-business-thinking/artifacts/verified-d22-report.html';
const html = readFileSync(reportPath, 'utf8');
const axeSource = readFileSync('node_modules/axe-core/axe.min.js', 'utf8');
const outDir = 'd23-evidence';
mkdirSync(outDir, {recursive:true});

const browser = await puppeteer.launch({
  executablePath: process.env.CHROME,
  headless: true,
  args: ['--no-sandbox', '--disable-dev-shm-usage']
});
const report = {artifact:reportPath, checks:{}, viewports:[], axe:[], errors:[]};
const page = await browser.newPage();
const errors = [];
page.on('pageerror', e => errors.push('pageerror: '+e.message));
page.on('request', req => errors.push('network-request: '+req.url()));
page.on('console', msg => {if(msg.type()==='error') errors.push('console: '+msg.text())});
const mark=(id,body)=>{report.checks[id]=body?'PASS':'FAIL';if(!body)report.errors.push('FAILED '+id);};
async function sizeCheck(width, height, label){
  await page.setViewport({width,height,deviceScaleFactor:1,isMobile:width<=390,hasTouch:width<=390});
  await page.setContent(html,{waitUntil:'load'});
  const metrics=await page.evaluate(()=>{
    const viewport=document.documentElement.clientWidth;
    const wrappers=[...document.querySelectorAll('.table-wrap')];
    return {
      ready:document.readyState,
      viewport,
      documentWidth:document.documentElement.scrollWidth,
      bodyWidth:document.body.scrollWidth,
      h1Text:document.querySelector('h1')?.innerText.trim()||'',
      sections:[...document.querySelectorAll('main section')].length,
      tables:wrappers.map(w=>({
        client:w.clientWidth,scroll:w.scrollWidth,
        overflow:getComputedStyle(w).overflowX,
        tableWidth:w.querySelector('table')?.getBoundingClientRect().width||0
      })),
      details:[...document.querySelectorAll('details')].map(x=>x.open),
      scripts:document.querySelectorAll('script').length,
      sheet:!!document.querySelector('main.shell'),
      glyphDistinct:(()=>{
        const c=document.createElement('canvas');c.width=72;c.height=64;
        const ctx=c.getContext('2d');ctx.font='32px "Noto Sans CJK SC", sans-serif';
        const draw=char=>{
          ctx.clearRect(0,0,72,64);ctx.fillText(char,8,45);
          return new Uint8ClampedArray(ctx.getImageData(0,0,72,64).data);
        };
        const x=draw('中'),y=draw('测');
        let delta=0;for(let i=0;i<x.length;i++)if(x[i]!==y[i])delta++;
        return delta>50;
      })()
    };
  });
  mark('ready_'+label,metrics.ready==='complete'&&metrics.sheet&&metrics.h1Text.length>12);
  mark('content_'+label,metrics.sections>=4 && metrics.tables.length===2 && metrics.details.length===2);
  mark('no_page_overflow_'+label,
    metrics.documentWidth<=metrics.viewport+1 && metrics.bodyWidth<=metrics.viewport+1);
  mark('table_scrolling_'+label,
    metrics.tables.every(t=>t.scroll>=t.client && t.overflow==='auto')
    && (width>760 || metrics.tables.every(t=>t.scroll>t.client+1)));
  mark('no_async_scripts_'+label,metrics.scripts===0&&metrics.details.every(x=>!x));
  mark('cjk_glyph_rendering_'+label,metrics.glyphDistinct);
  await page.screenshot({path:join(outDir,label+'.png'),fullPage:true});
  await page.addScriptTag({content:axeSource});
  const axe=await page.evaluate(async()=>await window.axe.run(document,{
    runOnly:{type:'tag',values:['wcag2a','wcag2aa','wcag21a','wcag21aa','wcag22aa']},
    rules:{'color-contrast':{enabled:true}}
  }));
  report.axe.push({
    viewport:label,violations:axe.violations.map(v=>({
      id:v.id,impact:v.impact,targets:v.nodes.map(n=>n.target.join(' ')).slice(0,8),
      description:v.help
    }))
  });
  report.viewports.push({name:label,...metrics});
  mark('accessibility_'+label,axe.violations.length===0);
}
try{
  for(const [width,height,label] of [
    [1440,900,'desktop_1440'],[390,844,'mobile_390'],[320,720,'reflow_320']
  ]) await sizeCheck(width,height,label);
  await page.setViewport({width:390,height:844,deviceScaleFactor:1,isMobile:true,hasTouch:true});
  await page.setContent(html,{waitUntil:'load'});
  const sections=await page.$$('details');
  mark('audit_sections_present',sections.length===2);
  await page.click('details:first-of-type summary');
  let status=await page.evaluate(()=>({
    open:document.querySelector('details')?.open,
    sql:document.querySelector('#sql-source')?.innerText||''
  }));
  mark('audit_mouse_toggle',status.open&&status.sql.includes('WITH per_direction'));
  await page.click('details:first-of-type summary');
  mark('audit_mouse_close',!(await page.$eval('details',e=>e.open)));
  await page.focus('details:nth-of-type(2) summary');
  await page.keyboard.press('Enter');
  mark('audit_keyboard_enter',await page.$eval('details:nth-of-type(2)',e=>e.open));
  await page.keyboard.press('Enter');
  mark('audit_keyboard_close',!(await page.$eval('details:nth-of-type(2)',e=>e.open)));
  mark('offline_no_network',errors.filter(x=>x.startsWith('network-request')).length===0);
  mark('no_js_runtime_errors',errors.filter(x=>!x.startsWith('network-request')).length===0);
  mark('no_dashboard_leak',!html.includes('data-content-ref="dashboard"'));
  mark('report_only',html.includes('D22 · Report-only')&&html.includes('历史数据 · Report'));
  await page.screenshot({path:join(outDir,'audit_closed_mobile.png'),fullPage:true});
} catch(e){
  report.errors.push(e.stack||String(e));
} finally {
  await browser.close();
  writeFileSync(join(outDir,'results.json'),JSON.stringify(report,null,2));
}
console.log('D23_QA_RESULT '+JSON.stringify({
  checks:report.checks,violations:report.axe,errors:[...errors,...report.errors],viewports:report.viewports.map(x=>({
    name:x.name,documentWidth:x.documentWidth,viewport:x.viewport,tables:x.tables
  }))
}));
if(report.errors.length||errors.length||report.axe.some(x=>x.violations.length)){
  process.exitCode=1;
}else{
  console.log('PASS: D23 browser rendering, responsive, audit interaction, accessibility, offline readiness');
}
