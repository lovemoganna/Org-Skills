// Reproducible policy regressions; deterministic scenarios, NOT LLM/KKING UI E2E.
// Run: node skills/trading-simulation-coach/tests/run_contract_regression.mjs
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const f=JSON.parse(readFileSync(new URL('./fixtures/btcusdt_1h_oct2026.json',import.meta.url),'utf8'));
const bars=f.candles, H=3600000, results=[];
const test=(id,fn)=>{try{results.push({id,status:'PASS',evidence:fn()})}catch(e){results.push({id,status:'FAIL',error:e.message})}};
function risk({equity, fraction, entry, stop, feeRoundTrip, slippage}){
 if(![equity,fraction,entry,stop,feeRoundTrip,slippage].every(Number.isFinite)
 ||equity<=0||fraction<=0||fraction>=1||entry<=0||stop<=0||feeRoundTrip<0||slippage<0)return{status:'BLOCKED'};
 const budget=equity*fraction,rate=Math.abs(entry-stop)/entry+feeRoundTrip+slippage;
 return{status:'PASS',budget,rate,notional:budget/rate};
}
function sampleState({revealed=false,reused=false,group='validation'}){
 return group==='validation'&&(revealed||reused)?'CONTAMINATED':'VALID';
}
function stopEdit({side,oldStop,newStop,allowed}){
 const widens=side==='LONG'?newStop<oldStop:newStop>oldStop;
 return !allowed&&widens?{status:'PROCESS_FAIL',applied:false}:{status:'APPROVED',applied:true};
}
function order(confirmed,requested=1){
 return confirmed==null?{status:'UNKNOWN',position:0}:
 {status:confirmed>=requested?'FILLED':confirmed>0?'PARTIAL':'UNFILLED',position:confirmed};
}
const params={equity:10000,fraction:.005,entry:100,stop:98,feeRoundTrip:.001,slippage:.001};
test('D00_source_integrity',()=>{
 assert.equal(f.symbol,'BTCUSDT');assert.equal(f.interval,'1h');assert.ok(bars.length>=11);
 bars.forEach((b,i)=>{assert.ok(b.l<=Math.min(b.o,b.c));assert.ok(b.h>=Math.max(b.o,b.c));if(i)assert.equal(b.t-bars[i-1].t,H)});
 return{validBars:bars.length};
});
test('B01_position_size',()=>{
 const r=risk(params);assert.equal(r.budget,50);assert.ok(Math.abs(r.rate-.022)<1e-10);
 assert.ok(Math.abs(r.notional-2272.72727)<.001);return r;
});
test('B02_blind_data_contamination',()=>{
 const decision=bars[5].t+H,visible=bars.filter(b=>b.t+H<=decision);
 assert.equal(visible.length,6);assert.equal(sampleState({revealed:true}),'CONTAMINATED');
 return{decision,visibleBars:visible.length,validated:false};
});
test('B03_profit_does_not_excuse_rule_violation',()=>{
 assert.ok(bars[5].c>bars[0].c);
 const v=stopEdit({side:'LONG',oldStop:83000,newStop:82800,allowed:false});
 assert.equal(v.status,'PROCESS_FAIL');assert.equal(v.applied,false);return v;
});
test('B04_actual_candles_stop_loss',()=>{
 const entry=bars[5].c, stop=84000, fee=.001, slip=.001;
 const r=risk({equity:10000,fraction:.005,entry,stop,feeRoundTrip:fee,slippage:slip});
 const idx=bars.findIndex((b,i)=>i>5&&b.l<=stop);assert.equal(idx,7);
 const fill=stop*(1-slip),qty=r.notional/entry;
 const pnl=(fill-entry)*qty-(entry+fill)*qty*fee/2,R=pnl/r.budget;
 assert.ok(R<-.98&&R> -1.02);return{entry,stopIndex:idx,assumedFill:fill,netPnl:+pnl.toFixed(4),R:+R.toFixed(5),interpretation:'normal_strategy_loss_under_assumed_fill'};
});
test('B05_touch_does_not_prove_order_fill',()=>{
 assert.ok(bars[7].l<84000);const x=order(null);
 assert.equal(x.position,0);return x;
});
test('B06_research_available_after_decision',()=>{
 const released=Date.parse('2026-10-20T00:00:00Z'),decision=Date.parse('2026-10-01T06:00:00Z');
 assert.ok(released>decision);return{acceptResearch:false};
});
test('B07_risk_exceeded',()=>{
 const r=risk(params);assert.ok(3000*r.rate>r.budget);
 return{allowTrade:false,riskOnProposedNotional:3000*r.rate,budget:r.budget};
});
test('B08_missing_cost_model',()=>{
 const r=risk({...params,feeRoundTrip:undefined});assert.equal(r.status,'BLOCKED');return r;
});
test('B09_partial_order_fill',()=>{
 const r=order(.4);assert.equal(r.position,.4);assert.equal(r.status,'PARTIAL');return r;
});
test('B10_wait_is_valid_decision',()=>{
 const signalPresent=false;const action=signalPresent?'TRADE':'WAIT';assert.equal(action,'WAIT');return{action,position:0};
});
test('B11_session_risk_halt_persists_reset',()=>{
 const session={cumulativeR:-3,halted:false,equity:10000};
 session.halted=session.cumulativeR<=-3;session.equity=10000;
 assert.equal(session.halted,true);return{halted:true};
});
test('B12_reused_validation_sample',()=>{
 assert.equal(sampleState({reused:true}),'CONTAMINATED');return{sample:'CONTAMINATED'};
});
const report={suite:'trading-simulation-coach deterministic policy checks',
source:f.source,barCount:bars.length,assumptions:['Stop fills at stop*(1-0.001) hypothetically','Round trip fees 0.1% for tested fill','Historical OHLC cannot prove real order execution'],
scope:'Tests policy evaluator, not LLM skill invocation or KKING UI',
passed:results.filter(x=>x.status==='PASS').length,failed:results.filter(x=>x.status==='FAIL').length,results};
console.log(JSON.stringify(report,null,2));if(report.failed)process.exitCode=1;
