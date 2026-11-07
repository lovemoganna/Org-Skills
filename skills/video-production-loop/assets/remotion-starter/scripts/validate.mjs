import fs from 'node:fs';
import {VideoSpec} from '../src/schema.mjs';
const file=process.argv[2]||'specs/example.json';
const spec=VideoSpec.parse(JSON.parse(fs.readFileSync(file,'utf8').replace(/^\uFEFF/,'')));
console.log(`Valid: ${spec.id}, ${spec.scenes.length} scenes, ${spec.scenes.reduce((n,s)=>n+s.seconds,0)} seconds`);
fs.writeFileSync('specs/VideoSpec.schema.json',JSON.stringify((await import('zod')).z.toJSONSchema(VideoSpec),null,2));
