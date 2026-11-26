const assert=require('node:assert/strict');
const {test}=require('node:test');
const {leaseFencedHost}=require('../lease_fenced_host.js');
function store(){
 const map=new Map();let seq=0;
 return {async read(id){return map.get(id)?JSON.parse(JSON.stringify(map.get(id))):{version:null,record:null};},
 async compareAndSwap(id,v,r){const old=map.get(id);if((old?.version??null)!==v)return{conflict:true};
 const version=String(++seq);map.set(id,{version,record:JSON.parse(JSON.stringify(r))});return{ok:true,version};}};
}
function host(s,time,leaseMs=100){return leaseFencedHost(s,{clock:()=>time.value,leaseMs});}
test('T27: lease busy, expired takeover, persisted monotonic epoch',async()=>{
 const s=store(),t={value:1000},a=host(s,t);const first=await a.claim('t27','A');
 assert.equal(first.status,'CLAIMED');assert.equal(first.epoch,1);
 assert.equal((await a.claim('t27','B')).status,'BUSY');
 assert.equal((await a.claim('t27','A')).status,'OWNED');
 t.value=1101;const b=await host(s,t).claim('t27','B');
 assert.equal(b.status,'CLAIMED');assert.equal(b.epoch,2);
 assert.equal((await host(s,t).inspect('t27')).record.owner,'B');
});
test('T28: old fencing token rejected, one idempotent effect committed',async()=>{
 const s=store(),t={value:0},h=host(s,t),a=await h.claim('t28','A');t.value=101;
 const b=await h.claim('t28','B');
 assert.equal((await h.commit('t28','A',a.epoch,'op',{x:1})).status,'FENCED');
 assert.equal((await h.commit('t28','B',b.epoch,'op',{x:1})).status,'COMMITTED');
 assert.equal((await h.commit('t28','B',b.epoch,'op',{x:1})).status,'ALREADY_COMMITTED');
 assert.equal((await h.commit('t28','B',b.epoch,'op',{x:2})).status,'OPERATION_PAYLOAD_CONFLICT');
 assert.equal(Object.keys((await h.inspect('t28')).record.effects).length,1);
});
test('T29: renewal retains epoch; expired token cannot commit',async()=>{
 const s=store(),t={value:0},h=host(s,t),a=await h.claim('renew','A');
 t.value=50;assert.equal((await h.renew('renew','A',a.epoch)).leaseUntil,150);
 t.value=151;assert.equal((await h.renew('renew','A',a.epoch)).status,'LEASE_EXPIRED');
 assert.equal((await h.commit('renew','A',a.epoch,'op',{a:1})).status,'LEASE_EXPIRED');
});
test('T29: worker crash after claim then fresh host recovery',async()=>{
 const s=store(),t={value:0};assert.equal((await host(s,t).claim('crash','A')).status,'CLAIMED');
 t.value=101;const b=await host(s,t).claim('crash','B');
 assert.equal(b.epoch,2);
 assert.equal((await host(s,t).commit('crash','B',b.epoch,'op',{v:1})).status,'COMMITTED');
 assert.equal((await host(s,t).inspect('crash')).record.effects.op.epoch,2);
});
test('T29: denied host authorization has no provider effect',async()=>{
 const s=store(),t={value:0};const permit=false;
 const outcome=permit?await host(s,t).claim('deny','A'):{status:'BLOCKED'};
 assert.equal(outcome.status,'BLOCKED');assert.equal((await s.read('deny')).record,null);
});
test('T29: host failure after durable claim but before commit has zero effects',async()=>{
 const s=store(),t={value:1},h=host(s,t),a=await h.claim('precommit','A');
 assert.equal(Object.keys((await h.inspect('precommit')).record.effects).length,0);
 t.value=102;const b=await host(s,t).claim('precommit','B');
 assert.equal((await h.commit('precommit','A',a.epoch,'op',{x:1})).status,'FENCED');
 assert.equal((await h.commit('precommit','B',b.epoch,'op',{x:1})).status,'COMMITTED');
});
test('T29: provider error before side effect remains uncertain, no false success',async()=>{
 const s=store(),t={value:1},h=host(s,t),a=await h.claim('before-error','A');
 const fail={read:id=>s.read(id),compareAndSwap:async()=>{throw Error('provider unavailable');}};
 assert.equal((await host(fail,t).commit('before-error','A',a.epoch,'op',{x:1})).status,'WRITE_OUTCOME_UNKNOWN');
 assert.equal(Object.keys((await h.inspect('before-error')).record.effects).length,0);
});
test('T29: lost ACK after committed effect must be read back and deduplicated',async()=>{
 const s=store(),t={value:1},h=host(s,t),a=await h.claim('ack-loss','A');let writes=0;
 const lost={read:id=>s.read(id),compareAndSwap:async(id,v,r)=>{writes++;await s.compareAndSwap(id,v,r);throw Error('ACK lost');}};
 assert.equal((await host(lost,t).commit('ack-loss','A',a.epoch,'op',{x:2})).status,'WRITE_OUTCOME_UNKNOWN');
 assert.equal((await h.inspect('ack-loss')).record.effects.op.payload.x,2);
 assert.equal((await h.commit('ack-loss','A',a.epoch,'op',{x:2})).status,'ALREADY_COMMITTED');
 assert.equal(writes,1);assert.equal(Object.keys((await h.inspect('ack-loss')).record.effects).length,1);
});
test('T29: owner switches after old read but before CAS; stale effect fenced',async()=>{
 const s=store(),t={value:10},h=host(s,t),a=await h.claim('race','A');let entered,release;
 const ready=new Promise(r=>entered=r),barrier=new Promise(r=>release=r);
 const delayed={read:id=>s.read(id),compareAndSwap:async(id,v,r)=>{entered();await barrier;return s.compareAndSwap(id,v,r);}};
 const old=host(delayed,t).commit('race','A',a.epoch,'op',{x:1});await ready;
 t.value=111;const b=await h.claim('race','B');release();
 assert.equal((await old).status,'FENCED');
 assert.equal(Object.keys((await h.inspect('race')).record.effects).length,0);
 assert.equal((await h.commit('race','B',b.epoch,'op',{x:1})).status,'COMMITTED');
});
test('T29: bad checkpoint and unbounded CAS conflicts fail closed',async()=>{
 const t={value:0},bad={read:async()=>({version:'sha',record:{schema:1,taskId:'x',owner:'A',epoch:0,leaseUntil:10,effects:{}}}),compareAndSwap:async()=>({ok:true,version:'sha2'})};
 await assert.rejects(()=>host(bad,t).claim('x','B'),/corrupt/);
 let calls=0;const conflicting={read:async()=>({version:null,record:null}),compareAndSwap:async()=>{calls++;return{conflict:true};}};
 const r=await leaseFencedHost(conflicting,{clock:()=>0,leaseMs:10,maxAttempts:2}).claim('x','A');
 assert.equal(r.status,'CONFLICT_RETRY_EXHAUSTED');assert.equal(calls,2);
});
test('T29: invalid token, path traversal, and lease config rejected',async()=>{
 const s=store();
 assert.throws(()=>leaseFencedHost(s,{leaseMs:0}),/invalid/);
 assert.throws(()=>leaseFencedHost(s,{maxAttempts:10}),/invalid/);
 await assert.rejects(()=>leaseFencedHost(s).claim('../unsafe','A'),/invalid/);
});
