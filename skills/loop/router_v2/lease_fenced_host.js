/* Legion T27-T30 candidate: durable CAS lease and fencing for effects in ONE ledger.
 * A lease alone cannot fence a separate external write. Source is host-side, not a model Skill.
 */
function leaseFencedHost(store,opts={}) {
  if(!store||typeof store.read!=="function"||typeof store.compareAndSwap!=="function")
    throw Error("trusted atomic read/CAS store required");
  const clock=opts.clock||(()=>Date.now()),leaseMs=opts.leaseMs??30000,maxAttempts=opts.maxAttempts??3;
  if(typeof clock!=="function"||!Number.isSafeInteger(leaseMs)||leaseMs<1||leaseMs>3600000||
     !Number.isSafeInteger(maxAttempts)||maxAttempts<1||maxAttempts>5)throw Error("invalid trusted lease settings");
  const copy=v=>JSON.parse(JSON.stringify(v));
  const valid=x=>typeof x==="string"&&/^[a-zA-Z0-9_.:-]{1,120}$/.test(x);
  const now=()=>{const t=clock();if(!Number.isSafeInteger(t)||t<0)throw Error("invalid trusted clock");return t;};
  async function load(id){
    const s=await store.read(id);
    if(!s||s.record==null)return {version:null,record:null};
    const r=s.record;
    if(typeof s.version!=="string"||!s.version||r.schema!==1||r.taskId!==id||!valid(r.owner)||
       !Number.isSafeInteger(r.epoch)||r.epoch<1||!Number.isSafeInteger(r.leaseUntil)||
       !r.effects||typeof r.effects!=="object"||Array.isArray(r.effects))
      throw Error("corrupt lease record; fail closed");
    return {version:s.version,record:copy(r)};
  }
  async function cas(id,original,next){
    try{
      const x=await store.compareAndSwap(id,original.version,copy(next));
      if(x?.ok===true&&typeof x.version==="string"&&x.version)return {status:"SUCCESS",version:x.version};
      if(x?.conflict===true)return {status:"CONFLICT"};
    }catch(_){}
    return {status:"WRITE_OUTCOME_UNKNOWN"};
  }
  async function claim(id,owner){
    if(!valid(id)||!valid(owner))throw Error("invalid task/owner");
    for(let i=0;i<maxAttempts;i++){
      const s=await load(id),t=now(),p=s.record;
      if(p&&p.leaseUntil>t){
        return p.owner===owner?{status:"OWNED",taskId:id,owner,epoch:p.epoch,leaseUntil:p.leaseUntil}:
          {status:"BUSY",taskId:id,currentOwner:p.owner,epoch:p.epoch,leaseUntil:p.leaseUntil};
      }
      const epoch=(p?.epoch||0)+1;
      const next={schema:1,taskId:id,owner,epoch,leaseUntil:t+leaseMs,effects:p?.effects||{}};
      const x=await cas(id,s,next);
      if(x.status==="SUCCESS")return {status:"CLAIMED",taskId:id,owner,epoch,leaseUntil:next.leaseUntil,version:x.version};
      if(x.status!=="CONFLICT")return {status:"WRITE_OUTCOME_UNKNOWN",taskId:id};
    }
    return {status:"CONFLICT_RETRY_EXHAUSTED",taskId:id};
  }
  async function renew(id,owner,epoch){
    if(!valid(id)||!valid(owner)||!Number.isSafeInteger(epoch))throw Error("invalid token");
    for(let i=0;i<maxAttempts;i++){
      const s=await load(id),r=s.record,t=now();
      if(!r||r.owner!==owner||r.epoch!==epoch)return {status:"FENCED"};
      if(r.leaseUntil<=t)return {status:"LEASE_EXPIRED"};
      const next={...r,leaseUntil:t+leaseMs};
      const x=await cas(id,s,next);
      if(x.status==="SUCCESS")return {status:"RENEWED",epoch,leaseUntil:next.leaseUntil};
      if(x.status!=="CONFLICT")return {status:"WRITE_OUTCOME_UNKNOWN"};
    }
    return {status:"CONFLICT_RETRY_EXHAUSTED"};
  }
  async function commit(id,owner,epoch,operationId,payload){
    if(!valid(id)||!valid(owner)||!Number.isSafeInteger(epoch)||epoch<1||!valid(operationId))
      throw Error("invalid commit identity");
    if(payload===undefined)throw Error("payload required");
    const data=copy(payload);
    for(let i=0;i<maxAttempts;i++){
      const s=await load(id),r=s.record,t=now();
      if(!r||r.owner!==owner||r.epoch!==epoch)return {status:"FENCED"};
      if(r.leaseUntil<=t)return {status:"LEASE_EXPIRED"};
      const old=Object.prototype.hasOwnProperty.call(r.effects,operationId)?r.effects[operationId]:null;
      if(old)return JSON.stringify(old.payload)===JSON.stringify(data)?
        {status:"ALREADY_COMMITTED",operationId,epoch:old.epoch}:{status:"OPERATION_PAYLOAD_CONFLICT",operationId};
      const next={...r,effects:{...r.effects,[operationId]:{owner,epoch,payload:data,at:t}}};
      const x=await cas(id,s,next);
      if(x.status==="SUCCESS")return {status:"COMMITTED",operationId,epoch,version:x.version};
      if(x.status!=="CONFLICT")return {status:"WRITE_OUTCOME_UNKNOWN",operationId};
    }
    return {status:"CONFLICT_RETRY_EXHAUSTED",operationId};
  }
  async function inspect(id){if(!valid(id))throw Error("invalid task");return load(id);}
  return {claim,renew,commit,inspect};
}
// GitHub Contents API is a *single-resource* CAS ledger, NOT a distributed transaction.
function githubLeaseStore(tools,{repository,branch,prefix="skills/loop/router_v2/evidence/leases"}={}) {
  if(!repository||!/^[\w.-]+\/[\w.-]+$/.test(repository)||!branch||typeof branch!=="string"||
     !prefix||typeof prefix!=="string")throw Error("explicit repository, branch and prefix required");
  const path=id=>prefix+"/"+id+".json";
  const result=x=>x?.result??x?.structuredContent?.result??x?.structuredContent??x;
  return {
    async read(id){
      try{
        const x=result(await tools.mcp__GitHub__fetch_file({repository_full_name:repository,path:path(id),ref:branch}));
        if(typeof x.content!=="string"||typeof x.sha!=="string")throw Error("invalid GitHub read response");
        return {version:x.sha,record:JSON.parse(x.content)};
      }catch(e){
        if(/NOT_FOUND|GitHub API error 404/i.test(String(e)))return {version:null,record:null};
        throw e;
      }
    },
    async compareAndSwap(id,expected,next){
      const args={repository_full_name:repository,path:path(id),branch,content:JSON.stringify(next,null,2)+"\n",
        message:"test(legion): CAS ledger "+id+" epoch "+next.epoch};
      if(expected===null){
        const ack=result(await tools.mcp__GitHub__create_file(args));
        if(!ack?.commit_sha)throw Error("create ACK missing");
        const observed=await this.read(id);
        if(observed.record?.owner!==next.owner||observed.record?.epoch!==next.epoch)throw Error("post-commit mismatch");
        return {ok:true,version:observed.version};
      }
      const ack=result(await tools.mcp__GitHub__update_file({...args,sha:expected}));
      if(!ack?.commit_sha||!ack?.content_sha)throw Error("update ACK missing");
      return {ok:true,version:ack.content_sha};
    }
  };
}
if(typeof module!=="undefined")module.exports={leaseFencedHost,githubLeaseStore};
