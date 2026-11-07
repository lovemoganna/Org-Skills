import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {bundle} from '@remotion/bundler';
import {selectComposition,renderMedia} from '@remotion/renderer';
import {VideoSpec} from '../src/schema.mjs';
const spec=VideoSpec.parse(JSON.parse(fs.readFileSync(process.argv[2]||'specs/example.json','utf8').replace(/^\uFEFF/,'')));
for(const s of (spec.narrationEnabled === false ? [] : spec.scenes)){const p=path.join('public',s.audio);if(!fs.existsSync(p))throw Error(`Missing ${p}; run npm run audio`);const d=Number(execFileSync('ffprobe',['-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',p],{encoding:'utf8'}));if(!Number.isFinite(d)||d>s.seconds+0.04)throw Error(`Audio exceeds scene: ${p}`);}
if(spec.bgm&&!fs.existsSync(path.join('public',spec.bgm.src)))throw Error('Missing BGM: '+spec.bgm.src);
fs.mkdirSync('renders',{recursive:true});
const start=Date.now();
const serveUrl=await bundle({entryPoint:path.resolve('src/index.tsx')});
const inputProps={spec};
const composition=await selectComposition({serveUrl,id:'KnowledgeVideo',inputProps});
let last=-1;
await renderMedia({composition,serveUrl,inputProps,codec:'h264',audioCodec:'aac',pixelFormat:'yuv420p',crf:18,concurrency:2,outputLocation:`renders/${spec.id}.mp4`,onProgress:({progress})=>{const p=Math.floor(progress*10);if(p!==last){console.log(`Rendering ${p*10}%`);last=p;}}});
fs.writeFileSync('renders/render-log.json',JSON.stringify({completedAt:new Date().toISOString(),elapsedSeconds:(Date.now()-start)/1000,node:process.version,remotion:'4.0.541',spec,frames:composition.durationInFrames},null,2));
console.log(`Rendered renders/${spec.id}.mp4`);
